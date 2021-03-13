from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin

from django.core.files.uploadedfile import InMemoryUploadedFile

from product.owner import OwnerListView, OwnerDetailView, OwnerCreateView, OwnerUpdateView, OwnerDeleteView

from product.models import Product, Comment, Fav
from product.forms import CreateForm, CommentForm
from django.contrib.humanize.templatetags.humanize import naturaltime

from product.utils import dump_queries
from django.db.models import Q


class ProductListView(OwnerListView):
    model = Product
    # By convention:
    template_name = "products/product_list.html"

    def get(self, request) :
        strval =  request.GET.get("search", False)
        favorites = None
        if strval :
            # Simple title-only search
            # objects = Post.objects.filter(title__contains=strval).select_related().order_by('-updated_at')[:10]

            # Multi-field search
            query = Q(title__contains=strval)
            query.add(Q(text__contains=strval), Q.OR)
            objects = Product.objects.filter(query).select_related().order_by('-updated_at')[:10]
        else:
            objects = Product.objects.all()
            favorites = list()
            if request.user.is_authenticated:
                # rows = [{'id': 2}, {'id': 4} ... ]  (A list of rows)
                rows = request.user.favorite_products.values('id')
                # favorites = [2, 4, ...] using list comprehension
                favorites = [ row['id'] for row in rows ]


            # Augment the post_list
        for obj in objects:
            obj.natural_updated = naturaltime(obj.updated_at)

        ctx = {'product_list' : objects, 'search': strval, 'favorites': favorites}
        retval = render(request, self.template_name, ctx)

        dump_queries()
        return retval;

class ProductDetailView(OwnerDetailView):
    model = Product
    template_name = 'products/product_detail.html'
    def get(self, request, pk) :
        x = Product.objects.get(id=pk)
        comments = Comment.objects.filter(product=x).order_by('-updated_at')
        comment_form = CommentForm()
        context = { 'product' : x, 'comments': comments, 'comment_product': comment_form }
        return render(request, self.template_name, context)


class ProductCreateView(OwnerCreateView):
    template_name = 'products/product_form.html'
    success_url = reverse_lazy('products:all')

    def get(self, request, pk=None):
        form = CreateForm()
        ctx = {'form': form}
        return render(request, self.template_name, ctx)

    def post(self, request, pk=None):
        form = CreateForm(request.POST, request.FILES or None)

        if not form.is_valid():
            ctx = {'form': form}
            return render(request, self.template_name, ctx)

        # Add owner to the model before saving
        pic = form.save(commit=False)
        pic.owner = self.request.user
        pic.save()
        return redirect(self.success_url)


class ProductUpdateView(OwnerUpdateView):
    template_name = 'products/product_form.html'
    success_url = reverse_lazy('products:all')

    def get(self, request, pk):
        pic = get_object_or_404(Product, id=pk, owner=self.request.user)
        form = CreateForm(instance=pic)
        ctx = {'form': form}
        return render(request, self.template_name, ctx)

    def post(self, request, pk=None):
        pic = get_object_or_404(Product, id=pk, owner=self.request.user)
        form = CreateForm(request.POST, request.FILES or None, instance=pic)

        if not form.is_valid():
            ctx = {'form': form}
            return render(request, self.template_name, ctx)

        pic = form.save(commit=False)
        pic.save()

        return redirect(self.success_url)

class ProductDeleteView(OwnerDeleteView):
    model = Product

class CommentCreateView(LoginRequiredMixin, View):
    def post(self, request, pk) :
        product = get_object_or_404(Product, id=pk)
        comment = Comment(text=request.POST['comment'], owner=request.user, product=product)
        comment.save()
        return redirect(reverse('products:product_detail', args=[pk]))

class CommentDeleteView(OwnerDeleteView):
    model = Comment
    template_name = "products/comment_delete.html"

    # https://stackoverflow.com/questions/26290415/deleteview-with-a-dynamic-success-url-dependent-on-id
    def get_success_url(self):
        product = self.object.product
        return reverse('products:product_detail', args=[product.id])



def stream_file(request, pk):
    product = get_object_or_404(Product, id=pk)
    response = HttpResponse()
    response['Content-Type'] = product.content_type
    response['Content-Length'] = len(product.picture)
    response.write(product.picture)
    return response

# csrf exemption in class based views
# https://stackoverflow.com/questions/16458166/how-to-disable-djangos-csrf-validation
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.utils import IntegrityError

@method_decorator(csrf_exempt, name='dispatch')
class AddFavoriteView(LoginRequiredMixin, View):
    def post(self, request, pk) :
        print("Add PK",pk)
        t = get_object_or_404(Product, id=pk)
        fav = Fav(user=request.user, product=t)
        try:
            fav.save()  # In case of duplicate key
        except IntegrityError as e:
            pass
        return HttpResponse()

@method_decorator(csrf_exempt, name='dispatch')
class DeleteFavoriteView(LoginRequiredMixin, View):
    def post(self, request, pk) :
        print("Delete PK",pk)
        t = get_object_or_404(Product, id=pk)
        try:
            fav = Fav.objects.get(user=request.user, product=t).delete()
        except Fav.DoesNotExist as e:
            pass

        return HttpResponse()

