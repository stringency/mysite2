"""
URL configuration for mysite2 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path
from app1.views import index, function, API, community, about, admin, account
from django.views.static import serve
from django.conf import settings

urlpatterns = [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}, name='media'),
    # path("admin/", admin.site.urls),

    # 管理员登录
    path("admin/register", admin.admin_register),
    # 管理员主页
    path("admin/index", admin.admin_index),
    # 前台流量
    path("admin/indexfront", admin.admin_indexfront),

    # 登录
    path("login/", account.login),

    # 主页
    path("index/", index.index),

    # 功能
    path("function/", function.index),
    # 图片风格转换功能
    path("function/funTranPic/", function.funTranPic),

    # API
    path("API/", API.index),
    path("API/soundCode/", API.soundCode),
    path("API/soundCode/TranPic/", API.soundCodeTranPic),

    # 社区
    path("community/", community.index),
    path("community/soundCodeCommunity/", community.soundCodeCommunity),
    path("community/soundCodeCommunity/communityTranPic/", community.communityTranPic),

    # 关于
    path("about/", about.index),

]
