FROM nginx:latest

COPY my-site /
COPY my-site.conf /etc/nginx/conf.d/

WORKDIR /

CMD ["service", "nginx", "start"]
