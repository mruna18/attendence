from django.db import models

# Create your models here.

class ShiftHeadType(models.Model):
    code = models.CharField(max_length=50, unique=True,blank=True, null=True)  # e.g., 'GENERAL'
    name = models.CharField(max_length=100,blank=True, null=True)              # e.g., 'General'
    description = models.TextField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Shift(models.Model):
    # company_id = models.ForeignKey(Company, on_delete=models.DO_NOTHING)
    company_id = models.IntegerField(blank=True, null=True)
    shift_head = models.ForeignKey(ShiftHeadType, on_delete=models.DO_NOTHING,blank=True, null=True)
    description = models.TextField(blank=True, null=True,)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

    def __str__(self):
        return f"{self.shift_head.name} (ID: {self.id})"
  

class SubShift(models.Model):
    shift = models.ForeignKey(Shift, on_delete=models.DO_NOTHING, related_name='subshifts',blank=True, null=True)
    title = models.CharField(max_length=100,blank=True, null=True)
    time_start = models.TimeField(blank=True, null=True)  
    time_end = models.TimeField(blank=True, null=True)    
    active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

    def __str__(self):
        return self.title