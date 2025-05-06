from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from events_available.models import Events_offline, Events_online
from events_cultural.models import Events_for_visiting, Attractions
    
# class AllEvents(models.Model):
#     event_atr = models.ForeignKey(to=Attractions, on_delete=models.CASCADE, verbose_name="Достопр", db_column='event_atr_id')

#     class Meta:
#         db_table = 'AllEvents'
#         verbose_name = 'Достопримечательности'
#         verbose_name_plural = 'Достопримечательности'

    # def __str__(self):
    #     return self.name
    
    # def display_id(self):
    #     return f'{self.id:05}'
        
    
	# event_online = models.ForeignKey('events_available.Events_online', on_delete=models.CASCADE, default=False)

	
# @receiver(post_save, sender=Attractions)
# def create_all_events_online(sender, instance, created, **kwargs): 
# 	if created:
# 		AllEvents.objects.create(event=instance)

# @receiver(post_save, sender=Attractions)
# def create_all_events_offline(sender, instance, created, **kwargs):
# 	if created:
# 		AllEvents.objects.create(event=instance)
	

