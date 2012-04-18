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

from PIL import Image as PIL_Image

ITEMS_PER_CATEGORY_PAGE=1

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
    global state
    state = '..........'

    categories=Category.objects.all()
    shared_books=Book.objects.filter(public_share=True)
    top_read=shared_books.order_by('-read_count')[:5]
    top_downloaded=shared_books.order_by('downloader_set.count')[:5]
    top_like=shared_books.order_by('vote_set.count')[:5]

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username = username, password = password)
            if user is not None:
                if user.is_active:
                    auth.login(request, user)
                    return render_to_response(
                        'user_page.html', RequestContext(request,{'user': user,})
                    )
            else:
                state ='Username and passowrd didn\'t match. Please try again.!'
                return render_to_response('main_page.html', RequestContext(request,{'state':state}))
    else:
        form = LoginForm()

    variables = RequestContext(request, {
        'Main_form': form,
        })
    return render_to_response(
        'main_page.html', variables)

def books(request):
    categories=Category.objects.all()
    books={}
    for category in categories:
        book_group=category.book_set.filter(public_share=True)
        books[category.name]=book_group.order_by('-upload_date')[:3]
    return render_to_response('books.html',RequestContext(request,{'categories':categories,'books':books}))

def are_friends(user,other_user):
    if user.friend_list.filter(friend=other_user).exists():
        return True
    return False
'''
def has_friend(user,other_user):
    for friend in user.friend_list.all():
        if not friend.is_waiting and friend.friend_id==other_user.id:
            return True
    return False
'''
def make_friend(request):
    if request.method=='GET':
        '''
        friend_request_user=request.user
        friend_response_user=get_object_or_404(User,id=request.GET['id'])
        new_friend=Friend.objects.create(
            host=friend_request_user,
            friend_id=request.GET['id'],
        )
        new_friend.save()
        friend_request_create(friend_response_user,friend_request_user)
        '''
        from_user=request.user
        to_user=get_object_or_404(User,id=request.GET['id'])
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

@login_required
def decline_friend(request,username):
    if request.user.username==username:
        if request.method=="GET":
            user=request.user
            from_user=get_object_or_404(User,id=request.GET['id'])

            friend_request=user.friend_request_list.get(from_user=from_user)
            friend_request.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))

@login_required
def get_friend_requests(request,username):
    if request.user.username==username:
        friend_request_list=request.user.friend_request_list.all()
        return render_to_response("User/friend_requests_page.html",RequestContext(request,{'friend_request_list':friend_request_list,}))
    else:raise Http404

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
    return render_to_response('user_page.html', variables)

def user_profile(request,username):
    if request.user.username!=username:
        return HttpResponseRedirect('/user/%s/profile'%request.user.username)
    else:
        user_info=request.user.user_information

        if user_info.gender==1:gender='m'
        elif user_info.gender==0:gender='f'
        else: gender=None

        if not user_info.birth_date:
            day=1
            month=1
            year=1912
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

@login_required
def user_password_change(request,username):
    user = get_object_or_404(User, username=username)
    user_info=user.user_information
    status=''
    if request.method=='POST':
        password_change_form=PasswordChangeForm(request.POST)
        if password_change_form.is_valid():
            old_password=password_change_form.cleaned_data['old_password']
            new_password=password_change_form.cleaned_data['new_password1']
            if user.check_password(old_password):
                user.set_password(new_password)
                status='Your password has been changed !'
            else:
                status='Your old password is not correct !'
    password_change_form=PasswordChangeForm()
    return render_to_response('password_change_page.html',RequestContext(request,{'form':password_change_form,'status':status}))

@login_required
def user_profile_config(request,username):
    user = get_object_or_404(User, username=username)
    if request.user==user:
        if request.method=="POST":
            info_form=UserInfoForm(request.POST)
            if info_form.is_valid():
                user_info=user.user_information

                user_info.first_name=info_form.cleaned_data['first_name']
                user_info.last_name=info_form.cleaned_data['last_name']

                gender=info_form.cleaned_data['gender']
                if gender=='m':user_info.gender=1
                else: user_info.gender=0

                user_info.about=info_form.cleaned_data['about']

                day=info_form.cleaned_data['day']
                month=info_form.cleaned_data['month']
                year=info_form.cleaned_data['year']
                birth_date=date(year,month,day)
                user_info.birth_date=birth_date

                user_info.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))
    '''
    user_info=user.user_information
    first_name=user_info.first_name
    last_name=user_info.last_name
    email=user.email
    if not request.method=='POST':
        form=UserInfoForm(initial={'first_name':first_name,'last_name':last_name,'email':email},label_suffix='')
    else :
        form=UserInfoForm(request.POST,label_suffix='')
    return render_to_response('User/user_config_page.html',RequestContext(request,{'form':form,}))
    '''
'''
@login_required
def user_info(request,username):
    user = get_object_or_404(User, username=username)
    user_info=user.user_information
    return render_to_response('User/user_info_page.html',RequestContext(request,{'user_info':user_info,}))
'''
from PIL import Image as PIL_Image
@login_required
def user_profile_image_change(request,username):
    user = get_object_or_404(User, username=username)
    user_info=user.user_information
    status=0
    img=None
    if request.method=='POST':
        image_change_form=ProfileImageChangeForm(request.POST,request.FILES)
        if image_change_form.is_valid():
            profile_img=image_change_form.cleaned_data['profile_image']
            user_info.image=profile_img
            status=1
            user_info.save()
            imfn = '/'.join([MEDIA_ROOT,'kien',profile_img.name])
            im = PIL_Image.open(imfn)
            im.thumbnail((200,200), Image.ANTIALIAS)
            im.save(imfn, "JPEG")

    else :
        status=2
        image_change_form=ProfileImageChangeForm()

    if user_info.image:
        img=user_info.image
    return render_to_response('profile_image_upload_page.html',RequestContext(request,{'form':image_change_form,'img':img,'status':status}))

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
    return render_to_response('register.html',variables)

def tag_cloud(request):
    categories=Category.objects.all()
    return render_to_response('tag_cloud.html',RequestContext(request,{
        'categories':categories,
    }))
def file_upload(request,upload_type):
    if upload_type=='book':
        return book_upload(request)
    if upload_type=='image':
        return option(request)
    if upload_type=='video':
        return AddVideo(request)
@login_required
def book_upload(request):
    if request.method=='POST':
        form=UploadFileForm(request.POST,request.FILES,label_suffix='')
        if form.is_valid():
            #uploadedFile = request.FILES['up_file']
            uploaded_file=form.cleaned_data['up_file']
            file_description=form.cleaned_data['description']
            file_category=form.cleaned_data['category']
            if form.cleaned_data['public_share']:file_share=True
            else: file_share=False

            file_name=uploaded_file.name

            created_book=Book.objects.create(
                uploader=request.user,
                title=file_name,
                category=file_category,
                file=uploaded_file,
                #thumbnail=thumbnail,
                description=file_description,
                public_share=file_share,
            )
            created_book.save()
            #thumbnail_option={'crop': True, 'size': (160, 120),}
            #thumbnail=ThumbnailerFieldFile(created_book.file)
            #created_book.thumbnail=thumbnail
            #created_book.save()
            status=4
                #return HttpResponseRedirect('/upload/success/')

            '''
            book,created_book=Book.objects.get_or_create(title=file_name)
            if not created_book :
                status=3
            else :
                created_book.category=file_category
                created_book.file=uploaded_file
                created_book.uploader=request.user
                created_book.description=file_description
                created_book.public_share=file_share
                created_book.save()
                status=4
            '''
        #form=UploadFileForm(label_suffix='')
        #title='a book'
        #return render_to_response('upload_page.html',RequestContext(request,{'form':form,'title':title,'status':status}))

    #else :
    form=UploadFileForm(label_suffix='')
    title='a book'
    status=2
    return render_to_response('book_upload_page.html',RequestContext(request,{'form':form,'title':title,'status':status}))

def file_upload_success(request):
    return render_to_response('successfully_upload_page.html')

from django.http import HttpResponse
from django.core.servers.basehttp import FileWrapper
import cStringIO

def file_download(request,book_id):
    book=Book.objects.get(id=int(book_id))
    downloaded_file=book.file
    #Can kiem tra file name, chinh file name thong qua split va splitext

    '''
    #Muon dung stringIO phai mo file ra roi ghi(mat cong,nhung nhanh)
    buffer_output=cStringIO.StringIO()
    for chunk in downloaded_file.chunks():
        buffer_output.write(chunk)
    buffer_output.close()
    response=HttpResponse(buffer_output, content_type='application/pdf')
    '''
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

MAIN_FIL='posted_date'
SUB_FIL='dec'
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
        '''
        paginator=Paginator(books,ITEMS_PER_CATEGORY_PAGE)
        try:
            current_page_books=paginator.page(page_index)
        except:
            raise Http404
        variables=RequestContext(request,{
            'form':filter_form,
            'category':category,
            'status':status,
            'books':books,
            'current_page_books':current_page_books,
            'show_paginator':paginator.num_pages>1,
            'has_prev':current_page_books.has_previous(),
            'has_next':current_page_books.has_next(),
            'page':page_index,
            'pages':paginator.num_pages,
            'next_page':page_index+1,
            'prev_page':page_index-1,
        })
        '''
        books=mk_paginator(request,books,2)
        #return render_to_response('category_page.html',variables)
        return render_to_response('Book/category_page.html',RequestContext(request,{'category':category,'books':books,'form':filter_form,'page':page}))

def book_page(request,category_name,book_id):
    category=get_object_or_404(Category,name=category_name)
    book=Book.objects.get(id=book_id)
    is_voted=has_voted(request.user,book)
    return render_to_response('Book/book_page.html',RequestContext(request,{'book':book,'is_voted':is_voted}))

def book_filter(category,main_filter,sub_filter):
    books=category.book_set.filter(public_share=True)
    if sub_filter == 'dec':
        if main_filter == 'posted_date':
            books=books.order_by('-upload_date')
            return books
        if main_filter == 'reading_number':
            books=books.order_by('-read_count')
            return books
        if main_filter == 'like_number':
            books=books.order_by('-num_voter')
            return books
        if main_filter == 'file_size':
            #books=books.order_by('-file_size')
            books=sorted(books,key=lambda book:book.book_size(),reverse=True)
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

@login_required
def delete_book(request,book_id):
    book=get_object_or_404(Book,id=book_id)
    if book.uploader==request.user:
        book.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))

@login_required
def delete_image(request,image_id):
    image=get_object_or_404(Lib_Image,id=image_id)
    if image.uploader==request.user:
        image.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))

@login_required
def delete_video(request,video_id):
    video=get_object_or_404(Video,id=video_id)
    if video.uploader==request.user:
        video.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))

def mainForum(request):
    forums = Forum.objects.all()
    return render_to_response("Forum/main_forum.html", RequestContext(request,{'forums':forums, 'user':request.user,}))

def forum(request, pk):
    """Listing of threads in a forum."""
    if request.method=='POST':
        create_thread(request,pk)
    threads = Thread.objects.filter(forum=pk).order_by("-created")
    threads = mk_paginator(request, threads, 1)
    new_thread_form=NewThreadForm()
    return render_to_response("Forum/forum.html",RequestContext(request, {'threads':threads,'new_thread_form':new_thread_form}))

def thread(request,pk):
    """Listing posts in a thread"""
    if request.method=='POST':
        create_post(request,pk)
    thread=Thread.objects.get(pk=pk)
    posts=Post.objects.filter(thread=pk).order_by("-created")
    posts=mk_paginator(request,posts,2)
    title=thread.title

    #Luu lai thoi truy cap cuoi cung
    participated_thread=request.user.participated_thread_set.get(thread=thread)
    participated_thread.last_modify=datetime.now()
    participated_thread.save()
    '''
    if request.user==thread.creator:
        thread.notification=0
        thread.save()
    '''
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
        #thread.notification+=1

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
                total_notifications.append(posts)
        return render_to_response('User/notifications_page.html',RequestContext(request,{'total_notifications':total_notifications,}))
    else:raise Http404
	
def AddVideo(request):
    if request.method == 'POST':
        form=AddVideoForm(request.POST)
        if form.is_valid():
            video_url=form.cleaned_data['url']
            video_description=form.cleaned_data['description']
            video_share=form.cleaned_data['public_share']
            video = Video.objects.create(
                url=video_url,
                description=video_description,
                public_share=video_share,
                uploader=request.user,
            )
            video.save()
            return HttpResponseRedirect("/video/")
        form=AddVideoForm()
    form=AddVideoForm()
    var=RequestContext(request,{
        'form':form
    })
    return render_to_response('Video/add_video.html',var)

def AddVideoSuccess(request):
    return render_to_response('Video/success.html')

def VideoPage(request):
    videos=Video.objects.all()
    var=RequestContext(request,{
        'videos': videos
    })
    return render_to_response('Video/video_page.html', var)

def option(request):
    return  render_to_response('Photos/option.html')

def uploadImage(request):
    if request.method == 'POST':
        form=UploadImageForm(request.POST,request.FILES)
        if form.is_valid():
            image_file=form.cleaned_data['up_file']
            image_description=form.cleaned_data['description']
            image_share=form.cleaned_data['public_share']

            image=Lib_Image.objects.create(
                image_file=image_file,
                uploader=request.user,
                description=image_description,
                public_share=image_share,
                url='',
            )
            image.save()
            url=image.image_file.url
            image.delete()
            image=Lib_Image.objects.create(
                image_file=image_file,
                uploader=request.user,
                description=image_description,
                public_share=image_share,
                url=url,
            )
            image.save()
            return HttpResponseRedirect("/image/")
        form=UploadImageForm()
    form=UploadImageForm()
    var=RequestContext(request,{
        'form':form
    })

    return render_to_response('Photos/uploadImage.html',var)


def addImage(request):
    if request.method=='POST':
        form=AddImageLinkForm(request.POST)
        if form.is_valid():
            image_url=form.cleaned_data['url']
            image_description=form.cleaned_data['description']
            image_share=form.cleaned_data['public_share']
            
            image=Lib_Image.objects.create(
                url=image_url,
                description=image_description,
                public_share=image_share,
                uploader=request.user,
            )
            
            image.save()
            return HttpResponseRedirect("/image/")
        form=AddImageLinkForm()
    form=AddImageLinkForm()
    var=RequestContext(request,{
        'form':form
    })
    return render_to_response("Photos/addImageLink.html",var)

def ImageDone(request):
    return render_to_response("Photos/success.html")
	
def ImagePage(request):
    images=Lib_Image.objects.all()
    var=RequestContext(request,{
        'images':images
    })
    return render_to_response('Photos/image_page.html',var)


