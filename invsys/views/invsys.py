from django.shortcuts import redirect, render
from django.views.generic import TemplateView


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
    
    else:
        return render(request, 'invsys/home.html')

def logoutuser(request):
    if request.method == 'POST':
        logout(request)
        return redirect('home')
