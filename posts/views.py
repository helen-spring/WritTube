from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.cache import cache_page
from .forms import PostForm, CommentForm
from .models import Post, Group, Comment, Follow

User = get_user_model()


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.all().select_related("group")
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        "index.html",
        {"page": page, "paginator": paginator}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        "group.html",
        {"group": group, "page": page, "paginator": paginator}
    )


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('index')
    return render(request, 'new_post.html', {'form': form, "edit": False})


def profile(request, username):
    user = get_object_or_404(User, username=username)
    user_posts = user.posts.all()
    followers = user.following.count()
    followings = user.follower.count()
    if request.user.is_authenticated:
        following = user.following.filter(user=request.user)
    else:
        following = False
    paginator = Paginator(user_posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'profile.html',
        {
            "page": page,
            "paginator": paginator,
            "profile_user": user,
            "user_posts": user_posts,
            "followers": followers,
            "followings": followings,
            "following": following
        }
    )


def post_view(request, username, post_id):
    post = get_object_or_404(
        Post,
        author__username=username,
        id=post_id
    )
    user_posts = post.author.posts.all()
    form = CommentForm()
    comments = post.comments.all()
    return render(
        request,
        'post.html',
        {
            "profile_user": post.author,
            "post": post,
            "user_posts": user_posts,
            "form": form,
            "comments": comments
        }
    )


@login_required
def post_edit(request, username, post_id):
    current_post = get_object_or_404(
        Post,
        author__username=username,
        id=post_id
    )
    if request.user != current_post.author:
        return redirect('post', username=username, post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=current_post
    )
    if form.is_valid():
        form.save()
        return redirect('post', username=username, post_id=post_id)
    return render(
        request,
        'new_post.html',
        {
            "form": form, "post": current_post, "edit": True
        }
    )


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def add_comment(request, username, post_id):
    current_post = get_object_or_404(
        Post,
        author__username=username,
        id=post_id
    )
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = current_post
        comment.author = request.user
        comment.save()
        return redirect('post', username=username, post_id=post_id)
    return redirect('post', username=username, post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(
        author__following__user=request.user
    )
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        "follow.html",
        {"page": page, "paginator": paginator}
    )


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author == request.user:
        return redirect('profile', username=username)
    if not author.following.filter(user=request.user).exists():
        Follow.objects.create(
            user=request.user,
            author=author
        )
        return redirect('follow_index')
    return redirect('follow_index')


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if author.following.filter(user=request.user):
        Follow.objects.filter(user=request.user, author=author).delete()
        return redirect('index')
    return redirect('profile', username=username)
