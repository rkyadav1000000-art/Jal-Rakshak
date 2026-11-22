from django.db import models


class PollutionReport(models.Model):
    CATEGORY_CHOICES = [
        ('water_contamination', 'Drinking Water Contamination'),
        ('waterlogging', 'Waterlogging'),
        ('river_pond_pollution', 'River and Pond Pollution'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=200)
    location = models.CharField(max_length=250)
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
    )
    description = models.TextField()
    photo = models.ImageField(
        upload_to='pollution_reports/',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class TapWaterTest(models.Model):
    state = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    block = models.CharField(max_length=100, blank=True)
    village = models.CharField(max_length=150)

    sample_date = models.DateField(null=True, blank=True)
    lab_name = models.CharField(max_length=200, blank=True)

    ph = models.FloatField(null=True, blank=True)
    tds = models.FloatField(null=True, blank=True)
    fluoride = models.FloatField(null=True, blank=True)
    nitrate = models.FloatField(null=True, blank=True)
    turbidity = models.FloatField(null=True, blank=True)

    # True = E. coli detected
    # False = E. coli absent
    # None = Test data unavailable
    e_coli_detected = models.BooleanField(null=True, blank=True,)
    source_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    arsenic = models.FloatField(null=True, blank=True)
    free_residual_chlorine = models.FloatField(null=True,blank=True)
    total_coliform_detected = models.BooleanField(null=True, blank=True)


    def __str__(self):
        return f"{self.village}, {self.district} - Tap Water"