FROM redis:4.0-alpine

RUN apk --no-cache add curl python py-setuptools py-pip wget unzip make g++ \
  && pip install rmtest

RUN cd /usr/src \
  && curl -SL https://github.com/RedisLabsModules/rejson/archive/v1.0.2.tar.gz \
    | tar -xz --strip-components 1 \
  && make all -j 4

# ---

FROM redis:4.0-alpine
RUN apk --no-cache add jq util-linux
COPY --from=0 /usr/src/src/rejson.so /usr/lib/redis/modules/

CMD ["redis-server", "--loadmodule", "/usr/lib/redis/modules/rejson.so"]
