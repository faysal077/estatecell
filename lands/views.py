# lands/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Land
from .forms import LandForm

def land_list(request):
    lands = Land.objects.all()
    return render(request, 'lands/land_list.html', {'lands': lands})

def land_create(request):
    if request.method == "POST":
        form = LandForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Land record created successfully!")
            return redirect('lands:land_list')
    else:
        form = LandForm()
    return render(request, 'lands/land_form.html', {'form': form, 'title': 'Add Land'})

def land_update(request, pk):
    land = get_object_or_404(Land, pk=pk)
    if request.method == "POST":
        form = LandForm(request.POST, instance=land)
        if form.is_valid():
            form.save()
            messages.success(request, "Land record updated successfully!")
            return redirect('lands:land_list')
    else:
        form = LandForm(instance=land)
    return render(request, 'lands/land_form.html', {'form': form, 'title': 'Edit Land'})

def land_delete(request, pk):
    land = get_object_or_404(Land, pk=pk)
    if request.method == "POST":
        land.delete()
        messages.success(request, "Land record deleted successfully!")
        return redirect('lands:land_list')
    return render(request, 'lands/land_confirm_delete.html', {'land': land})
