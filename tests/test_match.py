# -*-coding:utf8-*-
import random
import numpy
from web.matching import pairing
from web.models import User, Coordinate


def make_random_name():
    prefixes = (
        u'부주의한', u'경솔한', u'빠른', u'거만한', u'느린', u'겸손한', u'보통', u'잘생긴', u'멋진', u'못생긴',
        u'섹시한', u'미친', u'대단한', u'멍청한', u'똑똑한', u'이상한', u'천박한', u'하찮은', u'방탕한',
        u'욕심많은', u'이기적인', u'고집센', u'우직한', u'끔찍한', u'무시무시한', u'순수한', u'웅장한', u'위대한',
        u'상냥한', u'귀여운', u'쾌활한', u'온화한', u'사랑스러운', u'당당한', u'짜증나는', u'재치있는', u'음탕한',
        u'음란한', u'불건전한', u'건전한', u'건강한', u'합리적인', u'논리적인', u'감정적인', u'소심한', u'대범한',
        u'감기걸린', u'깨끗한', u'깔끔한', u'뻣뻣한', u'유연한', u'인자한', u'웃음많은', u'내성적인', u'사악한',
        u'병역기피', u'할말없는', u'눈치보는'
    )
    nations = (
        u'미국', u'토종', u'일본', u'중국', u'캐나다', u'가나', u'가봉', u'토고', u'독일', u'영국', u'러시아',
        u'인도', u'대만', u'홍콩', u'호주', u'네팔', u'칠레', u'북한', u'조선', u'고려', u'신라', u'터키',
        u'우즈벡', u'몽골', u'필리핀', u'이란', u'사우디', u'이집트', u'핀란드', u'이태리', u'스페인', u'프랑스',
        u'가나', u'수단', u'가봉', u'토고'
    )
    names = (
        u'사자', u'고양이', u'호랑이', u'재규어', u'곰', u'참새', u'하이애나', u'개', u'늑대', u'거북이', u'토끼',
        u'여우', u'고라니', u'숫사슴', u'암사슴', u'풍뎅이', u'미꾸라지', u'개구리', u'오리', u'거위', u'다람쥐',
        u'아나콘다', u'햄스터', u'피라냐', u'기린', u'코끼리', u'코뿔소', u'비버', u'돼지', u'멧돼지', u'닭',
        u'치타', u'상어', u'고래', u'돌고래', u'오징어', u'송사리', u'우파루파', u'자쿰', u'북극곰', u'사막여우',
        u'지렁이', u'지네', u'펭귄', u'미어캣', u'개미', u'개미핥기', u'양', u'두꺼비', u'원숭이', u'침팬지',
        u'오랑우탄', u'메뚜기', u'사오정', u'저팔계', u'손오공', u'이순신', u'앵무새', u'쥐', u'쇠똥구리'
    )
    prefix = random.sample(prefixes, 1)[0]
    nation = random.sample(nations, 1)[0]
    name = random.sample(names, 1)[0]
    return '%s %s %s' % (prefix, nation, name)


def test_pairing():
    groups = dict()
    for group in Coordinate.GROUPS.keys():
        groups[group] = list(Coordinate.scan(group__eq=group))

    users = []
    for x in xrange(300):
        university = random.sample(groups['university'], 1)[0].name
        user = User.put_item(
            username=make_random_name(),
            university=university,
            recruit_exp=random.randint(0, 3),
            goal_companies=[c.name for c in random.sample(groups['goal_companies'], 3)]
        )
        users.append(user)

    print '\n'
    pairs = pairing(users)
    for u1, u2 in pairs:
        u1 = [u for u in users if u.username == u1.username][0]
        u2 = [u for u in users if u.username == u2.username][0]
        print u1
        print u2
        print numpy.linalg.norm(numpy.array(u1.coordinates) - numpy.array(u2.coordinates))
        print
    assert 0