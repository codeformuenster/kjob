import redis
import json
import uuid
import datetime
import click


r = redis.StrictRedis(host='redis')

queues = ['created', 'claimed', 'finished', 'failed']


put_job_lua_script = """
local job_id = KEYS[1]
local new_queue = KEYS[2]
local old_queue = KEYS[3]
local job = ARGV[1]

local function merge(t1, t2)
    for k, v in pairs(t2) do
        if (type(v) == "table") and (type(t1[k] or false) == "table") then
            merge(t1[k], t2[k])
        else t1[k] = v end
    end
    return t1
end

if job_id == "" then
    job_id = redis.call('RPOP', old_queue)
    if not job_id then return nil end

    -- merge with given job ..
    local job_from_redis = redis.call('JSON.GET', job_id, '.')
    job = cjson.encode(merge(cjson.decode(job_from_redis), cjson.decode(job)))
end

if old_queue then
    redis.call('LREM', old_queue, 0, job_id)
end

redis.call('LPUSH', new_queue, job_id)
redis.call('JSON.SET', job_id, '.', job)

local _, _, key, queue_name = string.find(new_queue, "(%a+)%s*:%s*(%a+)")
redis.call('JSON.SET', job_id, '.queue', cjson.encode(queue_name))

return redis.call('JSON.GET', job_id, '.')
"""
put_job_lua = r.register_script(put_job_lua_script)


def put_to(job={}, queue='lost', **kwargs):

    old_queue = job.get('queue', 'created')

    base_fields = {
        "queue": queue,
        f"{queue}_when": datetime.datetime.utcnow().isoformat()
    }
    job = {**kwargs, **job, **base_fields}
    job_id = f"job:{job['id']}" if 'id' in job else ""

    keys = [job_id, f"queue:{queue}", f"queue:{old_queue}"]
    args = [json.dumps(job, ensure_ascii=False)]
    # return put_job_lua(keys=keys, args=args)
    return json.loads(put_job_lua(keys=keys, args=args))


@click.group()
def cli():
    pass


@cli.command()
@click.option('--command')
def create(command):
    job_id = str(uuid.uuid4())
    return put_to({}, 'created', id=job_id, command=command)


@cli.command()
def claim():
    job = put_to(queue='claimed')
    job_json = json.dumps(job, ensure_ascii=False)
    click.echo(job_json)


@cli.command()
@click.option('--job', help='In JSON as string.')
@click.option('--result')
def finish(job, result):
    job = json.loads(job)
    return put_to(job, 'finished', result=result)


@cli.command()
def info():
    info = {}
    for queue in queues:
        info[queue] = r.llen(f'queue:{queue}')

    click.echo(info)


@cli.command()
def fail(job, result):
    return put_to(job, 'failed', result=result)


if __name__ == '__main__':
    cli()
