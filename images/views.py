import redis
from actions.models import Action
from actions.utils import create_action
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, ListView, TemplateView

from .forms import ImageCreateForm, ImageUploadForm
from .models import Image

# connect to redis
r = redis.Redis(
    host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB
)


class ImageCreateView(LoginRequiredMixin, CreateView):
    form_class = ImageCreateForm
    template_name = "image/image/create.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["section"] = "images"
        return context

    def form_valid(self, form):
        cd = form.cleaned_data
        new_image = form.save(commit=False)
        new_image.user = self.request.user
        new_image.save()
        create_action(self.request.user, "bookmarked image", new_image)
        messages.success(self.request, "Image added successfully")
        return redirect(new_image.get_absolute_url())


class ImageUploadView(LoginRequiredMixin, CreateView):
    form_class = ImageUploadForm
    template_name = "images/image/upload.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["section"] = "images"
        return context

    def form_valid(self, form):
        cd = form.cleaned_data
        new_image = form.save(commit=False)
        new_image.user = self.request.user
        new_image.save()
        create_action(self.request.user, "bookmarked image", new_image)
        messages.success(self.request, "Image added successfully")
        return redirect(new_image.get_absolute_url())


class ImageDetailView(LoginRequiredMixin, DetailView):
    model = Image
    template_name = "images/image/detail.html"
    context_object_name = "image"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_object(self):
        obj = get_object_or_404(
            Image, id=self.kwargs.get("id"), slug=self.kwargs.get("slug")
        )
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        image = self.get_object()
        total_views = r.incr(f"image:{image.id}:views")
        r.zincrby("image_ranking", 1, image.id)
        context["total_views"] = total_views
        context["section"] = "images"
        return context


@method_decorator(require_POST, name="dispatch")
class ImageLikeView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        image_id = request.POST.get("id")
        action = request.POST.get("action")
        if image_id and action:
            try:
                image = Image.objects.get(id=image_id)
                if action == "like":
                    image.users_like.add(request.user)
                    create_action(request.user, "likes", image)
                else:
                    image.users_like.remove(request.user)
                    content_type = ContentType.objects.get_for_model(image)
                    Action.objects.filter(
                        user=request.user,
                        verb="likes",
                        target_ct=content_type,
                        target_id=image.id,
                    ).delete()

                return JsonResponse({"status": "ok"})
            except Image.DoesNotExist:
                pass
        return JsonResponse({"status": "error"})


class ImageListView(LoginRequiredMixin, ListView):
    model = Image
    paginate_by = 8
    template_name = "images/image/list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["section"] = "images"
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        images_only = self.request.GET.get("images_only")
        if images_only:
            self.template_name = "images/image/list_images.html"
        return queryset

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        paginator = self.get_paginator(self.object_list, self.paginate_by)
        page = request.GET.get("page")

        try:
            images = paginator.page(page)
        except PageNotAnInteger:
            images = paginator.page(1)
        except EmptyPage:
            if request.GET.get("images_only"):
                return HttpResponse("")
            images = paginator.page(paginator.num_pages)

        context = self.get_context_data(object_list=images)
        context["images"] = images

        return self.render_to_response(context)


class ImageRankingView(LoginRequiredMixin, TemplateView):
    template_name = "images/image/ranking.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        image_ranking = r.zrange("image_ranking", 0, -1, desc=True)[:10]  # type: ignore
        image_ranking_ids = [int(id) for id in image_ranking]
        # get most viewed images
        most_viewed = list(Image.objects.filter(id__in=image_ranking_ids))
        most_viewed.sort(key=lambda x: image_ranking_ids.index(x.id))  # type: ignore
        context["section"] = "images"
        context["most_viewed"] = most_viewed
        return context
