from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages, auth
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .models import Team, TeamUsers
from public.util import *


def home(request, tid):
    return render(request, 'base/home.html')
