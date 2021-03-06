# -*- coding:cp949 -*-

import os.path
from time import strftime, gmtime

from django.db import models
from django.db.models import Q
from django.db.models.fields import CharField, DateField, TextField, �
    DateTimeField
from django.db.models.fields.related import ForeignKey
from django.db.models.fields.files import ImageField
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, �
    PermissionsMixin

from bine.commons import get_category


class UserManager(BaseUserManager):
    def create_user(self, username, password, is_staff=False, is_superuser=False, **kwargs):
        if not username:
            raise ValueError('Users must have a valid authentication name.')

        if not kwargs.get('email'):
            raise ValueError('User must have a valid email.')

        if not kwargs.get('fullname'):
            raise ValueError('User must have a valid full name.')

        if not kwargs.get('birthday'):
            raise ValueError('User must have a valid birthday.')

        if not kwargs.get('sex'):
            raise ValueError('User must have a valid sex.')

        user = self.model(username=username,
                          email=self.normalize_email(kwargs.get('email')),
                          fullname=kwargs.get('fullname'),
                          birthday=kwargs.get('birthday'),
                          is_staff=is_staff,
                          is_active=True,
                          is_superuser=is_superuser,
                          sex=kwargs.get('sex'))

        user.set_password(password)
        user.save()

        return user

    def create_superuser(self, username, password, **kwargs):
        return self.create_user(username, password, True, True, **kwargs)


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=40, unique=True)
    email = models.EmailField(unique=True, blank=False)
    fullname = models.CharField(max_length=80, blank=False)
    birthday = models.DateField(blank=False)
    SEX_CHOICES = (
        ('M', '����'),
        ('F', '����'),
    )
    sex = models.CharField(max_length=1, choices=SEX_CHOICES, blank=False)
    tagline = models.CharField(max_length=128, blank=True)
    photo = models.ImageField(upload_to='authentication/%Y/%m/%d', blank=True)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    updated_on = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    friends = models.ManyToManyField('self', through='FriendRelation',
                                     symmetrical=False,
                                     related_name='related_to+')
    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'fullname', 'birthday', 'sex']

    def add_friend(self, friend, symm=True):
        friend_relation, created = FriendRelation.objects.get_or_create(
            from_user=self,
            to_user=friend)
        if symm:
            # avoid recursion by passing `symm=False`
            friend.add_friend(self, False)
        return friend_relation

    def remove_friend(self, friend, symm=True):
        FriendRelation.objects.filter(
            from_user=self,
            to_user=friend).delete()
        if symm:
            # avoid recursion by passing `symm=False`
            friend.remove_friend(self, False)

    def get_confirmed_friends(self):
        return FriendRelation.get_confirmed_friends(self)

    def get_unconfirmed_friends(self):
        return FriendRelation.get_unconfirmed_friends(self)

    def search_friend(self, query):
        users = User.objects.filter(Q(username__contains=query) | Q(fullname__contains=query))

        # Exclude self from search_list
        return users.exclude(Q(id=self.id) | Q(friends__id=self.id)).all()

    def get_recommended_friends(self):
        users = User.objects.all()

        # Exclude self and self's friends
        return users.exclude(Q(id=self.id) | Q(friends__id=self.id)).all()

    def get_user_and_friend_notes(self):
        """
            ���� ����ڿ� ģ������ ��Ʈ ����� �����Ѵ�.
        """
        return BookNote.objects.filter(Q(user=self) | Q(user__friends=self)).order_by('-created_at')[0:10]

    def to_json(self):
        json_data = {}
        if self.photo:
            json_data.update({'photo': self.photo.url})

        json_data.update({'id': self.id,
                          'username': self.username,
                          'fullname': self.fullname,
                          'birthday': self.birthday,
                          'sex': self.sex,
                          'tagline': self.tagline,
        })
        return json_data

    def __str__(self):
        return self.username

    def get_full_name(self):
        return self.fullname

    def get_short_name(self):
        return self.fullname

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        db_table = 'users'


class FriendRelation(models.Model):
    from_user = ForeignKey(User, related_name='from_user')
    to_user = ForeignKey(User, related_name='to_people')

    STATUS_CHOICES = (
        ('N', '���'),
        ('Y', '�¶�'),
        ('D', '����'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='N', blank=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_unconfirmed_friends(user):
        friend_relations = FriendRelation.objects.filter(from_user=user, status='N')
        return list(map(lambda x: x.to_user, friend_relations))

    def get_confirmed_friends(user):
        friend_relations = FriendRelation.objects.filter(from_user=user, status='Y')
        return list(map(lambda x: x.to_user, friend_relations))

    def __str__(self):
        return self.from_user.username + " - " + self.to_user.username

    class Meta:
        db_table = 'friend_relations'
        unique_together = ('from_user', 'to_user')


class BookCategory(models.Model):
    name = CharField(max_length=50, blank=False)

    updated_on = DateTimeField(auto_now=True)
    created_at = DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'book_categories'


class Book(models.Model):
    title = CharField(max_length=128, blank=False)
    category = CharField(max_length=128, blank=True)
    isbn = CharField(max_length=10, blank=True, unique=False)
    barcode = models.CharField(max_length=16, blank=False)
    author = CharField(max_length=128, blank=False)
    isbn13 = CharField(max_length=13, blank=False, unique=True)
    author_etc = CharField(max_length=128, blank=True)
    illustrator = CharField(max_length=128, blank=True)
    translator = CharField(max_length=50, blank=True)
    publisher = CharField(max_length=128, blank=True)
    pub_date = DateField(blank=True, null=True)
    description = TextField(blank=True)
    photo = models.URLField(blank=True)
    link = models.URLField(blank=True)
    updated_on = DateTimeField(auto_now=True)
    created_at = DateTimeField(auto_now_add=True)

    @staticmethod
    def get_recommended_books(user):
        category = get_category(user.birthday)
        return Book.objects.filter(category=category).order_by('-pub_date')

    def to_json(self):
        json_data = {}
        if self.photo:
            json_data.update({'photo': self.photo.url})

        json_data.update({'id': self.id,
                          'title': self.title,
                          'author': self.author,
                          'isbn': self.isbn,
                          'publisher': self.publisher,
                          'pub_date': self.pub_date,
                          'description': self.description,
        })
        return json_data

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'books'


def get_file_name(instance, filename):
    time = gmtime()
    path = strftime("note/%Y/%m/%d/", time)
    new_file_name = strftime("%Y%m%d-%X", time) + "-" + instance.user.username + os.path.splitext(filename)[1]
    return os.path.join(path, new_file_name)


class BookNote(models.Model):
    user = ForeignKey(User, related_name='booknotes')
    book = ForeignKey(Book, related_name='booknotes')

    read_date_from = DateField(null=False)
    read_date_to = DateField(null=False)

    content = TextField(blank=True)
    preference = CharField(max_length=1, blank=False, default=3)
    attach = ImageField(upload_to=get_file_name, blank=True, null=True)

    SHARE_CHOICES = (
        ('P', '����'),
        ('F', 'ģ��'),
        ('A', '���'),
    )

    share_to = CharField(max_length=1, choices=SHARE_CHOICES, blank=False, default='F')
    updated_on = DateTimeField(auto_now=True)
    created_at = DateTimeField(auto_now_add=True)

    def to_json(self):
        json_data = {}
        if self.attach:
            json_data.update({'attach': self.attach.url})

        json_data.update({'id': self.id,
                          'user': {'id': self.user.id,
                                   'username': self.user.username,
                                   'fullname': self.user.fullname},
                          'book': {'id': self.book.id,
                                   'title': self.book.title,
                                   'photo': self.book.photo.url, },
                          'content': self.content,
                          'preference': self.preference,
                          'read_date_from': self.read_date_from,
                          'read_date_to': self.read_date_to,
                          'share_to': self.share_to,
                          'likeit': self.likeit.count(),
                          'replies_count': self.replies.count(),
                          'created_at': self.created_at,
                          'updated_on': self.updated_on,
        })
        return json_data

    def __str__(self):
        return self.user.fullname + " - " + self.book.title

    class Meta:
        db_table = 'booknotes'
        ordering = ['-created_at']


class BookNoteLikeit(models.Model):
    user = ForeignKey(User, related_name='likeit')
    note = ForeignKey(BookNote, related_name='likeit')
    created_at = DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username + " - " + self.book.title

    class Meta:
        unique_together = (("user", "note"),)
        db_table = 'booknote_likeit'


class BookNoteReply(models.Model):
    user = ForeignKey(User, related_name='replies')
    note = ForeignKey(BookNote, related_name='replies')

    content = CharField(max_length=258, blank=False)

    updated_on = DateTimeField(auto_now=True)
    created_at = DateTimeField(auto_now_add=True)

    def to_json(self):
        json_obj = {'id': self.id,
                    'user': {'id': self.user.id,
                             'username': self.user.username,
                             'fullname': self.user.fullname},
                    'content': self.content,
                    'created_at': self.created_at,
        }
        return json_obj

    def __str__(self):
        return self.content

    class Meta:
        db_table = 'booknote_replies'  
