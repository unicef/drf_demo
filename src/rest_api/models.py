from django.db import models
from rest_framework.response import Response


class Office(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Program(models.Model):
    office = models.ForeignKey(Office, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Beneficiary(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)


class Plan(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    def approve(self):
        return ""

class Record(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    benefciary= models.ForeignKey(Beneficiary, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
