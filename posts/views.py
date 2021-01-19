from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User

POSTS_PER_PAGE = 10


def index(request):
    """view-функция для главной страницы."""
    post_list = Post.objects.select_related("group", "author")
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    context = {"page": page, "paginator": paginator}
    return render(request, "index.html", context)


def group_posts(request, slug):
    """view-функция для страницы сообщества."""
    group = get_object_or_404(Group, slug=slug)
    post_list = group.group_posts.all()
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    context = {"group": group, "page": page, "paginator": paginator}
    return render(request, "group.html", context)


@login_required
def new_post(request):
    """view-функция для создания нового поста."""
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == "GET" or not form.is_valid():
        context = {"form": form, "is_new": True}
        return render(request, "post_new.html", context)
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect("index")


def check_following(user, author):
    if user.is_authenticated:
        following = Follow.objects.filter(user=user, author=author).exists()
    else:
        following = False
    return following


def profile(request, username):
    """view-функция страницы автора."""
    author = get_object_or_404(User, username=username)
    author_posts_list = author.posts.all()
    paginator = Paginator(author_posts_list, POSTS_PER_PAGE)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    following = check_following(request.user, author)
    context = {
        "author": author,
        "page": page,
        "paginator": paginator,
        "following": following,
    }
    return render(request, "user/profile.html", context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(author=author, user=request.user)
    return redirect("profile", username=username)


@login_required
def profile_unfollow(request, username):
    unfollowed = Follow.objects.get(
        author__username=username,
        user=request.user)
    unfollowed.delete()
    return redirect("profile", username=username)


@login_required
def follow_index(request):
    """view-функция для страницы подписок пользователя."""
    post_list = Post.objects.select_related("author").filter(
        author__following__user=request.user)
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    context = {
        "page": page,
        "paginator": paginator,
    }
    return render(request, "follow.html", context)


def post_view(request, username, post_id):
    """view-функция одного поста."""
    post = get_object_or_404(
        Post.objects.select_related("author"),
        id=post_id,
        author__username=username)
    form = CommentForm(request.POST or None)
    following = check_following(request.user, post.author)
    context = {
        "author": post.author,
        "post": post,
        "comments": post.post_comments.all(),
        "form": form,
        "following": following,
    }
    return render(request, "user/post.html", context)


@login_required
def post_edit(request, username, post_id):
    """view-функция редактирования одного поста."""
    post = get_object_or_404(
        Post.objects.select_related("author"),
        id=post_id,
        author__username=username)
    if request.user == post.author:
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
            instance=post)
        if request.method == "GET" or not form.is_valid():
            context = {
                "post": post,
                "form": form,
                "is_new": False,
            }
            return render(request, "post_new.html", context)
        form.save()
    return redirect("post", username=username, post_id=post_id)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(
        Post.objects.select_related("author"),
        id=post_id,
        author__username=username)
    form = CommentForm(request.POST or None)
    if request.method == "GET" or not form.is_valid():
        context = {"post": post, "form": form, "is_new": False, }
        return render(request, "post_new.html", context)
    comment = form.save(commit=False)
    comment.post = post
    comment.author = request.user
    comment.save()
    context = {
        "author": post.author,
        "post": post,
        "comments": post.post_comments.all(),
        "form": form
    }
    return redirect("post", username=username, post_id=post_id)


def page_not_found(request, exception):
    """view-функция страницы ошибки 404."""
    return render(request, "misc/404.html", {"path": request.path}, status=404)


def server_error(request):
    """view-функция страницы ошибки 500."""
    return render(request, "misc/500.html", status=500)
