FROM python:2.7.9-slim

# Python optimization to run on docker
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

#tentativa 2
# RUN echo "deb [check-valid-until=no] http://archive.debian.org/debian jessie-backports main" > /etc/apt/sources.list.d/jessie-backports.list
# # As suggested by a user, for some people this line works instead of the first one. Use whichever works for your case
# # RUN echo "deb [check-valid-until=no] http://archive.debian.org/debian jessie main" > /etc/apt/sources.list.d/jessie.list
# RUN sed -i '/deb http:\/\/deb.debian.org\/debian jessie-updates main/d' /etc/apt/sources.list
# # RUN apt-get -o Acquire::Check-Valid-Until=false update
# RUN echo 'Acquire::Check-Valid-Until "false";' >> /etc/apt/apt.conf


# tentativa 1
# RUN echo "deb [check-valid-until=no] http://cdn-fastly.deb.debian.org/debian jessie main" > /etc/apt/sources.list.d/jessie.list
# RUN echo "deb [check-valid-until=no] http://archive.debian.org/debian jessie-backports main" > /etc/apt/sources.list.d/jessie-backports.list
# RUN sed -i '/deb http:\/\/deb.debian.org\/debian jessie-updates main/d' /etc/apt/sources.list
# RUN apt-get -o Acquire::Check-Valid-Until=false update

# Maybe run upgrade as well???

RUN rm /etc/apt/sources.list
RUN echo "deb http://archive.debian.org/debian/ jessie main" | tee -a /etc/apt/sources.list
RUN echo "deb-src http://archive.debian.org/debian/ jessie main" | tee -a /etc/apt/sources.list
RUN echo "Acquire::Check-Valid-Until false;" | tee -a /etc/apt/apt.conf.d/10-nocheckvalid
RUN echo 'Package: *\nPin: origin "archive.debian.org"\nPin-Priority: 500' | tee -a /etc/apt/preferences.d/10-archive-pin

RUN apt-get update
RUN apt-get install -y python-dev --force-yes
RUN apt-get install -y build-essential --force-yes

RUN pip install --upgrade pip==9.0.1
RUN pip install --upgrade pip
RUN pip install -U setuptools
RUN pip install --upgrade distribute

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# User, home, and app basics
RUN useradd --create-home app
WORKDIR /home/app
USER app

COPY . .

ARG build_info
RUN echo ${build_info} > build_info.txt


ENTRYPOINT [ "./gunicorn.sh" ]

# gunicorn --bind 0.0.0.0:$PORT --worker-class gevent --workers $WORKERS --log-file - host_provider.main:app
