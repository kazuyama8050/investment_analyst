# FROM --platform=linux/amd64 centos:7

# ENV container docker
# RUN (cd /lib/systemd/system/sysinit.target.wants/; for i in *; do [ $i == \
# systemd-tmpfiles-setup.service ] || rm -f $i; done); \
# rm -f /lib/systemd/system/multi-user.target.wants/*;\
# rm -f /etc/systemd/system/*.wants/*;\
# rm -f /lib/systemd/system/local-fs.target.wants/*; \
# rm -f /lib/systemd/system/sockets.target.wants/*udev*; \
# rm -f /lib/systemd/system/sockets.target.wants/*initctl*; \
# rm -f /lib/systemd/system/basic.target.wants/*;\
# rm -f /lib/systemd/system/anaconda.target.wants/*;
# VOLUME [ "/sys/fs/cgroup" ]

# # RUN localedef -f UTF-8 -i ja-JP ja-JP.UTF-8

# RUN apt -y update
# RUN apt -y install epel-release \
#     && apt -y install sudo crontabs gcc gcc-c++ libsshl2 openssh-server iproute openssl \
#     rpm-build autoconf bison git vim expect ansible posifix nkf wget jq \
#     man-db man-pages man-pages-ja tree whois rsyslog

# ENV LANG="ja_JP.UTF-8" \
#     LANGUAGE="ja_JP:ja" \
#     LC_ALL="ja_JP.UTF-8"

# COPY .vimrc /root/

# RUN echo 'ZONE="Asia/Tokyo"' > /etc/sysconfig/clock \
#     && \cp -f /usr/share/zoneinfo/Asia/Tokyo /etc/localtime

# RUN /usr/bin/systemctl enable sshd.service

# RUN /usr/bin/systemctl enable getty@tty1.service \
#     && /usr/bin/systemctl disable getty.target \
#     && /usr/bin/systemctl disable systemd-udevd service

# ENTRYPOINT /sbin/init

FROM ubuntu:22.04
# ENV container docker
# RUN (cd /lib/systemd/system/sysinit.target.wants/; for i in *; do [ $i == \
# systemd-tmpfiles-setup.service ] || rm -f $i; done); \
# rm -f /lib/systemd/system/multi-user.target.wants/*;\
# rm -f /etc/systemd/system/*.wants/*;\
# rm -f /lib/systemd/system/local-fs.target.wants/*; \
# rm -f /lib/systemd/system/sockets.target.wants/*udev*; \
# rm -f /lib/systemd/system/sockets.target.wants/*initctl*; \
# rm -f /lib/systemd/system/basic.target.wants/*;\
# rm -f /lib/systemd/system/anaconda.target.wants/*;

RUN apt -y update
RUN apt-get -y install systemd systemctl init sudo gcc openssh-server openssl \
    autoconf bison git vim expect ansible nkf wget jq \
    man-db tree whois rsyslog

# 以下ubuntuでインストールできなかったパッケージ
# Package 'httpd' has no installation candidate
# Unable to locate package crontabs
# Unable to locate package gcc-c+
# Unable to locate package libsshl2
# Package 'iproute' has no installation candidate
# Unable to locate package rpm-build
# Unable to locate package posifix
# Unable to locate package man-pages
# Unable to locate package man-pages-ja

ENV LANG="ja_JP.UTF-8" \
    LANGUAGE="ja_JP:ja" \
    LC_ALL="ja_JP.UTF-8"

COPY .vimrc /root/

# RUN echo 'ZONE="Asia/Tokyo"' > /etc/sysconfig/clock \
#     && \cp -f /usr/share/zoneinfo/Asia/Tokyo /etc/localtime

RUN echo "Asia/Tokyo" > /etc/timezone

# VOLUME [ "/sys/fs/cgroup" ]
# CMD ["/usr/sbin/init"]
# RUN /usr/bin/systemctl enable sshd.service

# RUN /usr/bin/systemctl enable getty@tty1.service \
#     && /usr/bin/systemctl disable getty.target \
#     && /usr/bin/systemctl disable systemd-udevd service

# ENTRYPOINT /sbin/init