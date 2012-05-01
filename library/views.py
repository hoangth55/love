from django.http import *
from library.forms import *

from django.http import  HttpResponseRedirect,HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext,Context
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from library.models import *
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib import auth
from settings import MEDIA_ROOT
from django.core.paginator import Paginator
from easy_thumbnails.files import *
from datetime import *
import operator
from PIL import Image as PIL_Image
from django.http import HttpResponse
from django.core.servers.basehttp import FileWrapper

from django.core.files.storage import default_storage

def mk_paginator(request,items,num_items):
    """Create and return a paginator"""
    paginator=Paginator(items,num_items)
    try: page= int(request.GET.get('page','1'))
    except ValueError: page=1

    try:
        items=paginator.page(page)
    except (InvalidPage,EmptyPage):
        items = paginator.page(paginator.num_pages)
    return items

def main_page(request):
    categories=Category.objects.all()
    shared_books=Book.objects.filter(public_share=True)
    top_read=shared_books.order_by('-read_count')[:5]
    top_downloaded=shared_books.order_by('downloader_set.count')[:5]
    top_like=shared_books.order_by('vote_set.count')[:5]
    return render_to_response('index.html', RequestContext(request,
        {'categories':categories,
         'top_read':top_read,
         'top_downloaded':top_downloaded,
         'top_like':top_like,
        }))

def are_friends(user,other_user):
    if user.friend_list.filter(friend=other_user).exists():
        return True
    return False

@login_required
def make_friend(request):
    if request.method=='GET':
        from_user=request.user
        to_user=get_object_or_404(User,id=request.GET['id'])
        if from_user is not to_user:
            if not from_user.friend_response_list.filter(to_user=to_user).exists():
                friend_request=Friend_Request.objects.create(
                    to_user=to_user,
                    from_user=from_user,
                )
                friend_request.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))

@login_required
def accept_friend(request,username):
    if request.user.username==username:
        if request.method=="GET":
            user=request.user
            from_user=get_object_or_404(User,id=request.GET['id'])
            if not user.friend_list.filter(friend=from_user).exists():
                friendship1=Friend.objects.create(
                    host=user,
                    friend=from_user,
                )
                friendship1.save()

                friendship2=Friend.objects.create(
                    host=from_user,
                    friend=user,
                )
                friendship2.save()

                friend_request=user.friend_request_list.get(from_user=from_user)
                friend_request.delete()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))
    else:
        return HttpResponseRedirect('/user/%s' %request.user.username)

@login_required
def decline_friend(request,username):
    if request.user.username==username:
        if request.method=="GET":
            user=request.user
            from_user=get_object_or_404(User,id=request.GET['id'])

            friend_request=user.friend_request_list.get(from_user=from_user)
            friend_request.delete()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))
    else:
        return HttpResponseRedirect('/user/%s' %request.user.username)

@login_required
def get_friend_requests(request,username):
    if request.user.username==username:
        friend_request_list=request.user.friend_request_list.all()
        return render_to_response("User/friend_requests_page.html",RequestContext(request,{'friend_request_list':friend_request_list,}))
    else:
        return HttpResponseRedirect('/user/%s' %request.user.username)

#----------------------------Phan User & User Media-------------------------------#
@login_required
def user_page(request,username):
    other_user = get_object_or_404(User, username=username)
    if request.user==other_user:
        is_user=True
        is_friend=False
        is_friend_request=False
    else:
        is_user=False
        if are_friends(request.user,other_user):
            is_friend=True
            is_friend_request=False
        else:
            is_friend=False
            if other_user.friend_request_list.filter(from_user=request.user).exists():
                is_friend_request=True
            else: is_friend_request=False

    variables=Context({
        'user':request.user,
        'other_user':other_user,
        'is_user':is_user,
        'is_friend':is_friend,
        'is_friend_request':is_friend_request,
    })
    return render_to_response('User/user_page.html', variables)

def user_book_page(request,username):
    if request.user.username==username:
        user=request.user
        books=user.book_list.all().order_by("-upload_date")
        books=mk_paginator(request,books,5)
        return render_to_response('User/user_book_page.html',RequestContext(request,{'books':books,}))
    else:
        return HttpResponseRedirect('/user/%s' %request.user.username)

def user_image_page(request,username):
    if request.user.username==username:
        user=request.user
        images=user.image_list.all().order_by("-upload_date")
        images=mk_paginator(request,images,5)
        return render_to_response('User/user_image_page.html',RequestContext(request,{'images':images,}))
    else:
        return HttpResponseRedirect('/user/%s' %request.user.username)


def user_video_page(request,username):
    if request.user.username==username:
        user=request.user
        videos=user.video_list.all().order_by("-upload_date")
        videos=mk_paginator(request,videos,5)
        return render_to_response('User/user_video_page.html',RequestContext(request,{'videos':videos,}))
    else:
        return HttpResponseRedirect('/user/%s' %request.user.username)

#----------------------------Het phan User & User Media-------------------------------#


#----------------------------Phan User Config-------------------------------#
@login_required
def user_profile(request,username):
    if request.user.username==username:
        if request.user.user_information:
            user_info=request.user.user_information
        else : user_info=User_Information.objects.create(user=request.user)

        if user_info.gender is None:gender=None
        elif user_info.gender:gender='m'
        else: gender='f'

        if not user_info.birth_date:
            day=''
            month=''
            year=''
        else:
            day=user_info.birth_date.day
            month=user_info.birth_date.month
            year=user_info.birth_date.year
        info_dict={
            'first_name':user_info.first_name,
            'last_name':user_info.last_name,
            'gender':gender,
            'about':user_info.about,
            'day':day,
            'month':month,
            'year':year,
        }
        info_form=UserInfoForm(label_suffix='',initial=info_dict)
        return render_to_response('User/user_profile_page.html',RequestContext(request,{'info_form':info_form}))
    else:
        return HttpResponseRedirect('/user/%s' %request.user.username)

@login_required
def user_profile_config(request,username):
    if request.user.username==username:
        user=request.user
        if request.method=="POST":
            info_form=UserInfoForm(request.POST)
            if info_form.is_valid():
                user_info=user.user_information

                user_info.first_name=info_form.cleaned_data['first_name']
                user_info.last_name=info_form.cleaned_data['last_name']

                gender=info_form.cleaned_data['gender']
                if gender=='m':user_info.gender=True
                else: user_info.gender=False

                day=int(info_form.cleaned_data['day'])
                month=int(info_form.cleaned_data['month'])
                year=int(info_form.cleaned_data['year'])
                birth_date=date(year,month,day)
                user_info.birth_date=birth_date

                user_info.about=info_form.cleaned_data['about']

                user_info.save()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))
    else:
        return HttpResponseRedirect('/user/%s' %request.user.username)

#Co van de
@login_required
def user_password_change(request,username):
    status=''
    if request.user.username==username:
        if request.method=='POST':
            password_change_form=PasswordChangeForm(request.POST)
            if password_change_form.is_valid():
                old_password=password_change_form.cleaned_data['old_password']
                new_password=password_change_form.cleaned_data['new_password1']
                if request.user.check_password(old_password):
                    request.user.set_password(new_password)
                    status='Your password has been changed successfully!'
                else:
                    status='Your old password is not correct !'
            else:
                status='The form is invalid !'
        password_change_form=PasswordChangeForm(label_suffix='')
        return render_to_response('User/user_password_change_page.html',RequestContext(request,{'password_change_form':password_change_form,'status':status,}))
    else:
        return HttpResponseRedirect('/user/%s' %request.user.username)

#Co van de
@login_required
def user_profile_image_change(request,username):
    if request.user.username==username:
        user_info=request.user.user_information
        if request.method=='POST':
            image_change_form=ProfileImageChangeForm(request.POST,request.FILES)
            if image_change_form.is_valid():
                profile_image=image_change_form.cleaned_data['profile_image']
                new_profile_image=User_Profile_Image.objects.create(
                    user=request.user,
                    profile_image=profile_image,
                )
                new_profile_image.save()

                #Cap nhap avatar trong user_information
                user_info.avatar=new_profile_image.id
                user_info.save()
                '''
                imfn = '/'.join([MEDIA_ROOT,'kien',profile_img.name])
                im = PIL_Image.open(imfn)
                im.thumbnail((200,200), PIL_Image.ANTIALIAS)
                im.save(imfn, "JPEG")
                '''
        image_change_form=ProfileImageChangeForm()

        if user_info.avatar: avatar_image=User_Profile_Image.objects.get(id=avatar).profile_image
        else: avatar_image=None
        return render_to_response('profile_image_upload_page.html',RequestContext(request,{'form':image_change_form,'avatar_image':avatar_image,}))
    else:
        return HttpResponseRedirect('/user/%s' %request.user.username)
#----------------------------Het phan User Config-------------------------------#

#-------------------------Phan login,logout,register-------------------------#

def login(request):
    status='This is form !'
    if request.method== "POST":
        login_form=LoginForm(request.POST,label_suffix='')
        if login_form.is_valid():
            login_username=login_form.cleaned_data['username']
            login_password=login_form.cleaned_data['password']
            user = auth.authenticate(username=login_username, password=login_password)
            if user is not None and user.is_active:
                auth.login(request, user)
                return HttpResponseRedirect('/user/'+login_username+'/')
            else:
                status="This user is not exits !"
        variables=RequestContext(request,{
            'form':LoginForm(),
            'status':status
        })
        return render_to_response('Account/login_page.html',variables)

    else :
        login_form=LoginForm(label_suffix='')
        variables= RequestContext(request,{
            'form':login_form,
            'status':status
        })
        return render_to_response('Account/login_page.html',variables)

def logout(request):
    auth.logout(request)
    return HttpResponseRedirect('/')

def register(request):
    auth.logout(request)
    if request.method == 'POST':
        form = RegistrationForm(request.POST,label_suffix='')
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1'],
                email=form.cleaned_data['email']
            )
            user.save()
            user_info=User_Information.objects.create(
                user=user,
            )
            user_info.save()
            return HttpResponseRedirect('/')
    else:
        form = RegistrationForm(label_suffix='')
    variables = RequestContext(request, {'form': form})
    return render_to_response('Account/register.html',variables)

#-------------------------Het phan login,logout,register-------------------------#

#---------------------------Phan upload-----------------------------#
def file_upload(request,upload_type):
    if upload_type=='book':
        return book_upload(request)
    if upload_type=='image':
        return image_upload(request)
    if upload_type=='image_link':
        return image_link_upload(request)
    if upload_type=='video_link':
        return video_link_upload(request)

@login_required
def book_upload(request):
    status=''
    if request.method=='POST':
        form=UploadBookForm(request.POST,request.FILES,label_suffix='')
        if form.is_valid():
            book_file=form.cleaned_data['up_file']
            book_description=form.cleaned_data['description']
            book_category=form.cleaned_data['category']
            if form.cleaned_data['public_share']:book_share=True
            else: book_share=False

            book_name=book_file.name

            book=Book.objects.create(
                uploader=request.user,
                title=book_name,
                category=book_category,
                book_file=book_file,
                description=book_description,
                public_share=book_share,
            )
            book.save()
            status='Your book has been successfully uploaded !'
        else: status='Your book upload has been canceled !'
    form=UploadBookForm(label_suffix='')
    variables=RequestContext(request,{
        'form':form,
        'status':status,
    })
    return render_to_response('Upload/book_upload_page.html',variables)

@login_required
def image_upload(request):
    status=''
    if request.method == 'POST':
        form=UploadImageForm(request.POST,request.FILES)
        if form.is_valid():
            image_title=form.cleaned_data['title']
            image_file=form.cleaned_data['up_file']
            image_description=form.cleaned_data['description']
            if form.cleaned_data['public_share']:image_share=True
            else: image_share=False

            image=Image.objects.create(
                title=image_title,
                image_file=image_file,
                uploader=request.user,
                description=image_description,
                public_share=image_share,
            )
            image.save()
            status='Your image has been successfully uploaded !'
        else: status='Your image upload has been canceled !'
    form=UploadImageForm(label_suffix='')
    variables=RequestContext(request,{
        'form':form,
        'status':status,
    })
    return render_to_response('Upload/image_upload_page.html',variables)

@login_required
def image_link_upload(request):
    status=''
    if request.method=='POST':
        form=UploadImageLinkForm(request.POST)
        if form.is_valid():
            image_title=form.cleaned_data['title']
            image_url=form.cleaned_data['link']
            image_description=form.cleaned_data['description']
            if form.cleaned_data['public_share']:image_share=True
            else: image_share=False

            image=Image.objects.create(
                title=image_title,
                url=image_url,
                description=image_description,
                public_share=image_share,
                uploader=request.user,
            )
            image.save()
            status='Your image link has been successfully uploaded !'
        else: status='Your image link upload has been canceled !'
    form=UploadImageLinkForm(label_suffix='')
    variables=RequestContext(request,{
        'form':form,
        'status':status,
    })
    return render_to_response("Upload/image_link_upload_page.html",variables)

def video_link_upload(request):
    status=''
    if request.method == 'POST':
        form=UploadVideoLinkForm(request.POST)
        if form.is_valid():
            video_title=form.cleaned_data['title']
            video_url=form.cleaned_data['link']
            video_description=form.cleaned_data['description']
            if form.cleaned_data['public_share']:video_share=True
            else: video_share=False

            video = Video.objects.create(
                title=video_title,
                url=video_url,
                uploader=request.user,
                description=video_description,
                public_share=video_share,

            )
            video.save()
            status='Your video link has been successfully uploaded !'
        else: status='Your video link upload has been canceled !'
    form=UploadVideoLinkForm(label_suffix='')
    variables=RequestContext(request,{
        'form':form,
        'status':status,
    })
    return render_to_response('Upload/video_link_upload_page.html',variables)

#---------------------------Het phan upload-----------------------------#


#---------------------------Phan delete ,set public-----------------------------#

@login_required
def delete_book(request,book_id):
    book=get_object_or_404(Book,id=book_id)
    if book.uploader==request.user:
        book.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))

@login_required
def delete_image(request,image_id):
    image=get_object_or_404(Image,id=image_id)
    if image.uploader==request.user:
        image.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))

@login_required
def delete_video(request,video_id):
    video=get_object_or_404(Video,id=video_id)
    if video.uploader==request.user:
        video.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))

@login_required
def set_public_media_object(request,media_object_type,media_object_id):
    media_object=None
    if media_object_type=='book':
        media_object=get_object_or_404(Book,id=media_object_id)
    if media_object_type=='image':
        media_object=get_object_or_404(Image,id=media_object_id)
    if media_object_type=='video':
        media_object=get_object_or_404(Video,id=media_object_id)
    if media_object:
        media_object.public_share=True
        media_object.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))

@login_required
def set_private_media_object(request,media_object_type,media_object_id):
    media_object=None
    if media_object_type=='book':
        media_object=get_object_or_404(Book,id=media_object_id)
    if media_object_type=='image':
        media_object=get_object_or_404(Image,id=media_object_id)
    if media_object_type=='video':
        media_object=get_object_or_404(Video,id=media_object_id)
    if media_object:
        media_object.public_share=False
        media_object.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))

#---------------------------Het phan delete,set public-----------------------------#


#------------------------Phan Forum---------------------------#

def mainForum(request):
    forums = Forum.objects.all()
    return render_to_response("Forum/main_forum.html", RequestContext(request,{'forums':forums, 'user':request.user,}))

def forum(request, pk):
    if request.method=='POST':
        create_thread(request,pk)
    threads = Thread.objects.filter(forum=pk).order_by("-created")
    threads = mk_paginator(request, threads, 1)
    new_thread_form=NewThreadForm()
    return render_to_response("Forum/forum.html",RequestContext(request, {'threads':threads,'new_thread_form':new_thread_form}))

def thread(request,pk):
    if request.method=='POST':
        create_post(request,pk)
    thread=Thread.objects.get(pk=pk)
    posts=Post.objects.filter(thread=pk).order_by("-created")
    posts=mk_paginator(request,posts,2)
    title=thread.title

    #Luu lai thoi diem truy cap cuoi cung
    participated_thread=request.user.participated_thread_set.get(thread=thread)
    participated_thread.last_modify=datetime.now()
    participated_thread.save()

    reply_form=ReplyForm()
    return render_to_response("Forum/thread.html",RequestContext(request, {'posts':posts,'title':title,'reply_form':reply_form}))

@login_required
def create_post(request,pk):
    reply_form=ReplyForm(request.POST)
    if reply_form.is_valid():
        new_post=Post.objects.create(
            creator=request.user,
            created=datetime.now(),
            thread=Thread.objects.get(pk=pk),
            content=reply_form.cleaned_data['content'],
            link = reply_form.cleaned_data['attach_link'],
        )
        new_post.save()

        thread=Thread.objects.get(pk=pk)
        if not thread.participant_set.filter(participant=request.user).exists():
            new_thread_participant=Thread_Participant.objects.create(
                thread=thread,
                participant=request.user,
                last_modify=datetime.now()
            )
            new_thread_participant.save()
        else :
            thread_participant=thread.participant_set.get(participant=request.user)
            thread_participant.last_modify=datetime.now()
            thread_participant.save()

@login_required
def create_thread(request,pk):
    new_thread_form=NewThreadForm(request.POST)
    if new_thread_form.is_valid():
        new_thread=Thread.objects.create(
            creator=request.user,
            created=datetime.now(),
            forum=Forum.objects.get(pk=pk),
            title=new_thread_form.cleaned_data['subject'],
        )
        new_thread.save()

@login_required
def get_notifications(request,username):
    if request.user.username==username:
        participated_thread_set=request.user.participated_thread_set.all()
        total_notifications=[]
        if participated_thread_set is not None:
            for participated_thread in participated_thread_set:
                posts=participated_thread.thread.post_set.filter(created<participated_thread.last_modify)
                total_notifications.extend(posts)
        return render_to_response('User/notifications_page.html',RequestContext(request,{'total_notifications':total_notifications,}))
    else:
        return HttpResponseRedirect('/user/%s' %request.user.username)

#------------------------Het phan Forum---------------------------#

def has_voted(user,book):
    for vote in user.vote_set.all():
        if vote.book==book:return True
    else: return False

def save_vote(request):
    if request.method=='GET':
        book_id=request.GET['id']
        book=get_object_or_404(Book,pk=book_id)
        new_vote=Vote.objects.create(
            voter=request.user,
            book=book,
        )
        new_vote.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))

#------------------------Cac trang book ,image, video trong library-------------------#
def book_page(request):
    books=Book.objects.all().filter(public_share=True).order_by("-upload_date")
    books=mk_paginator(request,books,20)
    return render_to_response('Book/books_page.html',RequestContext(request,{'books':books,}))
def image_page(request):
    images=Image.objects.all().filter(public_share=True).order_by("-upload_date")
    images=mk_paginator(request,images,20)
    return render_to_response('Image/images_page.html',RequestContext(request,{'images':images,}))
def video_page(request):
    videos=Video.objects.all().filter(public_share=True).order_by("-upload_date")
    videos=mk_paginator(request,videos,20)
    return render_to_response('Video/videos_page.html',RequestContext(request,{'videos':videos,}))

@login_required
def book(request,book_id):
    book=get_object_or_404(Book,id=book_id)
    if book.public_share:
        return render_to_response('Book/book.html',RequestContext(request,{'book':book,}))
    else:
        return render_to_response('Book/book.html',RequestContext(request,{'book':None,}))

@login_required
def image(request,image_id):
    image=get_object_or_404(Image,id=image_id)
    if image.public_share:
        return render_to_response('Image/image.html',RequestContext(request,{'image':image,}))
    else:
        return render_to_response('Image/image.html',RequestContext(request,{'image':None,}))

@login_required
def video(request,video_id):
    video=get_object_or_404(Video,id=video_id)
    if video.public_share:
        return render_to_response('Video/video.html',RequestContext(request,{'video':video,}))
    else:
        return render_to_response('Video/video.html',RequestContext(request,{'video':None,}))
#------------------------Het cac trang book ,image, video trong library-------------------#
def search(request):
    searched_books=[]
    searched_images=[]
    searched_videos=[]
    show_result=False
    if request.method=='GET':
        if request.GET.has_key('query'):
            query=request.GET['query'].strip()
            query_word_set=query.split()

            if request.GET.has_key('book_search'):
                for query_word in query_word_set:
                    books=Book.objects.all().filter(title__icontains=query_word)
                    searched_books.extend(books)

            if request.GET.has_key('image_search'):
                for query_word in query_word_set:
                    images=Image.objects.all().filter(title__icontains=query_word)
                    searched_images.extend(images)
            if request.GET.has_key('video_search'):
                for query_word in query_word_set:
                    videos=Video.objects.all().filter(title__icontains=query_word)
                    searched_videos.extend(videos)

    variables={
        'show_result':show_result,
        'searched_books':searched_books,
        'searched_images':searched_images,
        'searched_videos':searched_videos,
    }
    return render_to_response('Search/search_page.html',RequestContext(request,variables))


def file_download(request,book_id):
    book=Book.objects.get(id=int(book_id))
    downloaded_file=book.book_file
    #Can kiem tra file name, chinh file name thong qua split va splitext
    response=HttpResponse(FileWrapper(downloaded_file), content_type='application/pdf')

    response['Content-Disposition'] = 'attachment; filename=%s' %downloaded_file.name

    return response


def library(request):
    categories=Category.objects.all()
    books={}
    for category in categories:
        book_group=category.book_set.filter(public_share=True)
        books[category.name]=book_group.order_by('-upload_date')[:3]
    return render_to_response('library.html',RequestContext(request,{'categories':categories,'books':books}))




def category(request,category_name):
    if not request.GET:
        return HttpResponseRedirect('/library/%s/?page=1' %category_name)
    else:
        try:
            page=int(request.GET['page'])
        except ObjectDoesNotExist:
            return Http404
        #return render_to_response('check_page.html',RequestContext(request,{'page':page}))

    page=int(request.GET['page'])
    category=get_object_or_404(Category,name=category_name)

    if request.POST:
        filter_form=FilterForm(request.POST,label_suffix='')
        if filter_form.is_valid():
            main_filter=filter_form.cleaned_data['main_filter']
            sub_filter=filter_form.cleaned_data['sub_filter']
            global MAIN_FIL,SUB_FIL
            MAIN_FIL=main_filter
            SUB_FIL=sub_filter
            filter_form.initial={'main_filter':MAIN_FIL,'sub_filter':SUB_FIL}
    else:
        filter_form=FilterForm(label_suffix='',initial={'main_filter':MAIN_FIL,'sub_filter':SUB_FIL})

    books=book_filter(category,MAIN_FIL,SUB_FIL)

    if books is None:
        status='There are no book in %s category' %category_name
        return render_to_response('Book/category_page.html',RequestContext(request,{'category':category,'status':status}))

    else:
        status='There are %s books in %s category' %(books.count(),category_name)
        books=mk_paginator(request,books,2)
        #return render_to_response('category_page.html',variables)
        return render_to_response('Book/category_page.html',RequestContext(request,{'category':category,'books':books,'form':filter_form,'page':page}))



#Can xem xet them
def video_page(request):
    videos=Video.objects.all()
    videos=videos.filter(public_share=True)
    is_vote=has_voted(request.user,video)
    return render_to_response('Video/videos_page.html',RequestContext(request,{'videos':videos,}))

def image_page(request):
    images=Image.objects.all()
    images=images.filter(public_share=True)
    return render_to_response('Image/images_page.html',{'images':images,})

def book_page(request,category_name,book_id):
    category=get_object_or_404(Category,name=category_name)
    book=Book.objects.get(id=book_id)
    is_voted=has_voted(request.user,book)
    return render_to_response('Book/books_page.html',RequestContext(request,{'book':book,'is_voted':is_voted}))

#Co van de
MAIN_FIL='upload_date'
SUB_FIL='dec'
def book_filter(category,main_filter,sub_filter):
    books=category.book_set.filter(public_share=True)
    if sub_filter == 'dec':
        if main_filter == 'upload_date':
            books=books.order_by('-upload_date')
            return books
        if main_filter == 'reading_number':
            books=books.order_by('-read_count')
            return books
        if main_filter == 'like_number':
            books=books.order_by('-num_voter')
            return books
        if main_filter == 'file_size':
            books=list(books)
            books.sort(key=operator.attrgetter())
            return books
    if sub_filter == 'inc':
        if main_filter == 'posted_date':
            books=books.order_by('upload_date')
            return books
        if main_filter == 'reading_number':
            books=books.order_by('read_count')
            return books
        if main_filter == 'like_number':
            books=books.order_by('num_voter')
            return books
        if main_filter == 'file_size':
            #books=books.order_by('file_size')
            books=sorted(books,key=lambda book:book.book_size())
            return books

