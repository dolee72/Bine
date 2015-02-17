import os.path
from time import strftime, gmtime

from django.db import models
from django.db.models.fields import CharField, DateField, TextField, \
    DateTimeField
from django.db.models.fields.related import ManyToManyField, ForeignKey
from django.db.models.fields.files import ImageField
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, \
    PermissionsMixin



# common utility functions
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
        ('M', '남자'),
        ('F', '여자'),
    )
    sex = models.CharField(max_length=1, choices=SEX_CHOICES, blank=False)
    tagline = models.CharField(max_length=128, blank=True)
    photo = models.ImageField(upload_to='authentication/%Y/%m/%d', blank=True)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    updated_on = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    friends = models.ManyToManyField('self', through='FriendLation',
                                     symmetrical=False,
                                     related_name='related_to+')
    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'fullname', 'birthday', 'sex']

    def add_friend(self, friend, symm=True):
        friend_relation, created = FriendLation.objects.get_or_create(
            from_person=self,
            to_person=friend)
        if symm:
            # avoid recursion by passing `symm=False`
            friend.add_friend(self, False)
        return friend_relation

    def remove_friend(self, friend, symm=True):
        FriendLation.objects.filter(
            from_person=self,
            to_person=friend).delete()
        if symm:
            # avoid recursion by passing `symm=False`
            friend.remove_relationship(self, False)

    def get_friends(self):
        return self.friends.filter(
            to_user__from_person=self)

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


class FriendLation(models.Model):
    from_user = ForeignKey(User, related_name='from_user')
    to_user = ForeignKey(User, related_name='to_people')
    created_at = models.DateTimeField(auto_now_add=True)

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
    categories = ManyToManyField(BookCategory, related_name='books')
    title = CharField(max_length=128, blank=False)
    isbn = CharField(max_length=15, blank=False, unique=True)
    author = CharField(max_length=50, blank=False)
    illustrator = CharField(max_length=50, blank=True)
    translator = CharField(max_length=50, blank=True)
    publisher = CharField(max_length=128, blank=True)
    pub_date = DateField(blank=True, null=True)
    page = CharField(max_length=4, blank=True)
    description = TextField(blank=True)
    content = TextField(blank=True)
    photo = ImageField(upload_to='book/%Y/%m/%d', blank=True)

    LANGUAGE_CHOICES = (
        ('ko', '한국어'),
        ('en', '영어'),
        ('jp', '일어'),
        ('cn', '중국'),
    )

    language = CharField(max_length=2, choices=LANGUAGE_CHOICES, default='ko', blank=False)

    AGE_LEVEL_CHOICES = (
        ('1', '0-3세'),
        ('2', '4-7세'),
        ('3', '초등1-2'),
        ('4', '초등3-4'),
        ('5', '초등5-6'),
        ('6', '청소년'),
        ('7', '성인'),
        ('8', '유아전체'),
        ('9', '초등전체'),
    )

    age_level = CharField(max_length=1, choices=AGE_LEVEL_CHOICES, default='9', blank=False)

    updated_on = DateTimeField(auto_now=True)
    created_at = DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

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
    attach = ImageField(upload_to=get_file_name, null=True)

    SHARE_CHOICES = (
        ('P', '개인'),
        ('F', '친구'),
        ('A', '모두'),
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
