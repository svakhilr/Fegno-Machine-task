from django.db import models
from users.models import User

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    

    class Meta:
        abstract = True


class ResourseCategory(BaseModel):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
    


class Resource(BaseModel):
    organisation = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resources')
    category = models.ForeignKey(ResourseCategory,on_delete=models.CASCADE,related_name='category')
    title = models.CharField(max_length=255)
    slot_interval = models.PositiveIntegerField()
    slot_start_time = models.TimeField()
    slot_end_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    def get_available_slots(self, date_input):
        from users.helper import generate_resource_slots
        return generate_resource_slots(self, date_input)


class Reservation(BaseModel):
    BOOKED = 'booked'
    CANCELLED = 'cancelled'
    
    status = (
        (BOOKED, 'Booked'),
        (CANCELLED, 'Cancelled'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservations')
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='reservations')
    booking_status = models.CharField(choices=status,max_length=10,default=BOOKED)
    booking_date = models.DateField()
    booking_slot_start_time = models.TimeField()
    booking_slot_end_time = models.TimeField()
    
        

