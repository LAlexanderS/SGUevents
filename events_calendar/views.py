from django.shortcuts import render

def index(request):
	return render(request, 'events_calendar/index.html')
