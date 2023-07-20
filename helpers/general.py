class Generator:
    def __init__(self, gen):
        self.gen = gen

    def __iter__(self):
        self.value = yield from self.gen

def get_free_sa(sa_map,file_size):
    ok_sas = []
    for i in sa_map:
        if 15784004812 - int(i['size']) >=file_size:
            ok_sas.append(int(i['_id']))
    return ok_sas

