from django.shortcuts import redirect, render
from django.views.generic import TemplateView
from django.contrib import messages
from django.contrib.auth import authenticate, login

class SignUpView(TemplateView):
    template_name = 'registration/signup.html'


def home(request):
    if request.user.is_authenticated:
        
        if request.user.is_assembly:
            return redirect('assembly:assembly_home')
        elif request.user.is_warehouse:
            return redirect('warehouse:warehouse_home')
        else:
            return redirect('planner:planner_home')
    
    elif request.method == "GET":
        return render(request, 'invsys/home.html')

    elif request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)

                if request.user.is_assembly:
                    return redirect('assembly:assembly_home')
                elif request.user.is_warehouse:
                    return redirect('warehouse:warehouse_home')
                else:
                    return redirect('planner:planner_home')
        else:
            error = 'username or password not correct'
            return render(request, 'invsys/home.html', {'error':error})

def logoutuser(request):
    if request.method == 'POST':
        logout(request)
        return redirect('home')