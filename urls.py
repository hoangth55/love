from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from library.views import *
from django.contrib import admin
from settings import MEDIA_ROOT
admin.autodiscover()

site_media=os.path.join(
    os.path.dirname(__file__),'site_media'
)
storage=MEDIA_ROOT

urlpatterns = patterns('',
    # Static folder
    url(r'^site_media/(?P<path>.*)$','django.views.static.serve',
            {'document_root': site_media }),
    (r'^storage/(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': storage}),

    #Admin doc
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),

    url(r'^$',main_page),

    #Login , logout ,register
    url(r'^accounts/login/$',login),
    url(r'^accounts/logout/$',logout),
    url(r'^register/$',register),
    #User page
    url(r'^user/(\w+)/$',user_page),
    url(r'^user/(\w+)/profile/$',user_profile),
    url(r'^user/(\w+)/profile_config/$',user_profile_config),
    url(r'^user/(\w+)/profile_image_change/$',user_profile_image_change),
    url(r'^user/(\w+)/password_change/$',user_password_change),
    url(r'^user/(\w+)/books',user_book_page),
    url(r'^user/(\w+)/images',user_image_page),
    url(r'^user/(\w+)/videos',user_video_page),

    #Notifications
    url(r'^user/(\w+)/notifications/$',get_notifications),

    #Friend requests and accept,decline
    url(r'^user/(\w+)/friend_requests/$',get_friend_requests),
    url(r'^user/(\w+)/friend_accept/$',accept_friend),
    url(r'^user/(\w+)/friend_decline/$',decline_friend),

    #Library
    url(r'^library/$',library),
    url(r'^library/(\w+)/$',category),
    url(r'^library/(\w+)/(\d+)',book_page),
    url(r'^library/images/$',image_page),
    url(r'^library/videos/$',video_page),

    #Delete
    url(r'^book_delete/(\d+)/$',delete_book),
    url(r'^image_delete/(\d+)/$',delete_image),
    url(r'^video_delete/(\d+)/$',delete_video),

    #Sharing
    url(r'^set_public/(\w+)/(\d+)/$',set_public_media_object),
    url(r'^set_private/(\w+)/(\d+)/$',set_private_media_object),


    #Test cloud
    #url(r'^tag_cloud/$',tag_cloud),

    #Upload
    url(r'^upload/(\w+)/$',file_upload),
    #url(r'^upload/success/$',file_upload_success),
    url(r'^download/(\d+)/$',file_download),

    url(r'^pdf_display/$',direct_to_template,{'template':'pdf_display.html'}),

    #Forum
    url(r'^forum/$',mainForum),
    url(r'^forum/(\d+)/$',forum),
    url(r'^thread/(\d+)/$',thread),

    #Friend
    url(r'make_friend/$',make_friend),

    #Vote
    url(r'vote/$',save_vote),


    #Video
    #url(r'^video/success/$',AddVideoSuccess),

    #Image
    url(r'^image/upload/$',image_upload),
    url(r'^image/add/$',image_link_upload),
    #url(r'^image/success/$',ImageDone),

    #url(r'^search/$',search),


)
