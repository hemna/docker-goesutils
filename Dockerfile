FROM ubuntu:18.10 AS goesutils
MAINTAINER Walter A. Boring IV <waboring@hemna.com>

ENV VERSION=1.0.0
ENV HOME=/home/goes
ENV BRANCH="master"
ARG UID=1000
ARG GID=1000

ENV INSTALL=$HOME/install
RUN apt-get -y update
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get install -y apt-utils pkg-config
RUN apt-get install -y wget python3 python3-pip git-core
RUN apt-get install -y imagemagick
RUN apt-get install -y inotify-tools
RUN apt-get install -y htop util-linux

# Add telegraf monitor agent
RUN wget -qO- https://repos.influxdata.com/influxdb.key | apt-key add -
RUN echo "deb https://repos.influxdata.com/debian stretch stable" | tee /etc/apt/sources.list.d/influxdb.list
RUN apt-get -y update
RUN apt-get install -y telegraf sudo
ADD conf/telegraf.conf /etc/telegraf

# Setup Timezone
ENV TZ=US/Eastern
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt-get install -y tzdata
RUN dpkg-reconfigure --frontend noninteractive tzdata

RUN apt-get install -y vim uuid sudo ffmpeg libasound2-plugins mencoder

RUN apt-get install python3 python3-pip
WORKDIR $HOME
ADD conf/requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

# Now change the imagemagic policies on sizes
RUN sed -i 's/256MiB/4GiB/g' /etc/ImageMagick-6/policy.xml
RUN sed -i 's/1GiB/4GiB/g' /etc/ImageMagick-6/policy.xml
RUN sed -i 's/512MiB/4GiB/g' /etc/ImageMagick-6/policy.xml
RUN sed -i 's/16KP/128KP/g' /etc/ImageMagick-6/policy.xml
RUN sed -i 's/128MB/1.037GP/g' /etc/ImageMagick-6/policy.xml

# override this to run another configuration
ENV CONF default

RUN addgroup --gid $GID goes
RUN useradd -m -u $UID -g $GID goes

ADD conf/monitor.conf bin/monitor.conf

COPY bin $HOME/bin
RUN chmod 755 $HOME/bin/run.sh

# Create directory to hold some of the install files.
RUN chmod 755 $HOME && cd $HOME && mkdir install
RUN chown -R goes:goes $HOME

VOLUME ["/home/goes/data"]

CMD $HOME/bin/run.sh
