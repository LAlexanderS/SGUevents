from django.urls import path, include
from users import views

app_name = 'users'

urlpatterns = [
	path('', views.index, name='index'),
  path('login/', views.log_in, name='login'),
	path('signup/', views.sign_up, name='signup')
]