from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import uuid


class Member(models.Model):
    member_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=80) 
    cost_incurred = models.DecimalField(
            max_digits=5,
            decimal_places=2,
            default=0.00
            )
    
    def __str__(self):
        """
        if self.book:
            return f'{self.name} borrowed {self.book.title},\
                    total cost: {self.cost_incurred} '
        else:
        """
        return f'{self.name}'
    
    class Meta:
        ordering = ['name']
      
    def get_absolute_url(self):
        return reverse('member_detail', args=[str(self.id)]) 
      
    def display_books_borrowed(self):
        return ','.join(
                [book.title for book in self.books_borrowed.all()]
                )
 
    def total_costs(self):
        """show total amount member owes"""
        total_cost = self.cost_incurred
        for transaction in self.history.all():
            total_cost += transaction.total_cost
        return total_cost


class Book(models.Model):
    class BookStatus(models.TextChoices):
        AVAILABLE = "AV", _("Available")
        UNAVAILABLE = "UN", _("Unavailable")

    book_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    isbn = models.CharField(max_length=200)
    year = models.IntegerField()
    genre = models.CharField(max_length=80)
    summary = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    status = models.CharField(
            max_length=2, 
            choices=BookStatus.choices,
            default=BookStatus.AVAILABLE,
            )
    cost = models.DecimalField(max_digits=5, decimal_places=2)
    borrower = models.ForeignKey(
            Member,
            on_delete=models.SET_NULL,
            null=True,
            blank=True
            )

    def __str__(self):
        return f'{self.title}'

    class Meta:
        ordering = ['title']

    def get_absolute_url(self):
        return reverse('book_detail', args=[str(self.id)])  


class BookTransaction(models.Model):
    member = models.ForeignKey(
            Member,
            on_delete=models.CASCADE,
            related_name='member_transaction'
            )
    book = models.ForeignKey(
            Book,
            on_delete=models.CASCADE,
            related_name='book_transaction'
            )
    date_borrowed = models.DateTimeField(auto_now_add=True)
    date_returned = models.DateTimeField(blank=True, null=True)
    returned = models.BooleanField(default=False)
    total_cost = models.DecimalField(
            max_digits=5,
            decimal_places=2,
            blank=True,
            null=True
            )
    borrowed_days = models.IntegerField(blank=True, null=True)

    def save(self, *args, **kwargs):
        self.borrowed_days = self.calc_borrowed_days()
        self.total_cost = self.calc_total_cost(self.borrowed_days)

        self.member.cost_incurred = self.total_cost

        super(BookTransaction, self).save(*args, **kwargs)

    def calc_borrowed_days(self):
        if self.date_returned:
            return (self.date_returned - self.date_borrowed).days
        else:
            return (timezone.now() - self.date_borrowed).days

    def calc_total_cost(self, borrowed_days):
        cost_per_day = self.book.cost
        return cost_per_day * borrowed_days
       
    def __str__(self):
        return f'{self.member.name} borrowed {self.book.title}'

    class Meta:
        ordering = ['date_borrowed']   
      
    def get_absolute_url(self):
        return reverse('transaction_detail', args=[str(self.id)])
