from ap import txt2list, train_test
from collections import defaultdict

def ngrams_list(sentence, n):
    beg = ['<s{}>'.format(i) for i in range(1,n)]
    end = ['</s{}>'.format(i) for i in range(1,n)]
    sentence = beg + sentence + end
    return list(zip(*(sentence[i:len(sentence)-n+i+1] for i in range(n))))

def ctxt_dy2(train):
    cdy = {'fw': defaultdict(lambda: defaultdict(int)),
           'bw': defaultdict(lambda: defaultdict(int))}
    for sentence in train:
        bigrams = ngrams_list(sentence, 2)
        for bigram in bigrams:
            cdy['fw'][bigram[:1]][bigram[1:]] += 1
            cdy['bw'][bigram[1:]][bigram[:1]] += 1
    # Convert cdy from defaultdict to dict (dr is direction i.e. 'fw' or 'bw')
    cdy = {dr: {ctxt: dict(cdy[dr][ctxt]) for ctxt in cdy[dr]} for dr in cdy}
    return cdy

def prob_dy2(train):
    cdy = ctxt_dy2(train)
    total_freq = sum(len(sentence) + 1 for sentence in train)
    pdy = defaultdict(lambda: defaultdict(dict))
    for ctxt in cdy['fw']:
        ctxt_freq = sum(cdy['fw'][ctxt].values())
        #pdy[ctxt]['jt'] = ctxt_freq / total_freq
        for goal in cdy['fw'][ctxt]:
            bigram_freq = cdy['fw'][ctxt][goal]
            goal_freq = sum(cdy['bw'][goal].values())
            probs = {'fw': bigram_freq / ctxt_freq,
                     'bw': bigram_freq / goal_freq,
                     'jt': bigram_freq / total_freq}
            pdy[ctxt][goal] = probs
    pdy = {ctxt: {goal: pdy[ctxt][goal] for goal in pdy[ctxt]} for ctxt in pdy}
    return (cdy, pdy)

def aps2(bigram, model):
    cdy, pdy = model
    ctxt, goal = (bigram.split()[0],), (bigram.split()[1],)
    # Z-shaped paths:
    lr_words = defaultdict(float)
    rl_words = defaultdict(float)
    z_paths = []
    for anl_goal in cdy['fw'][ctxt]:
        for anl_ctxt in cdy['bw'][anl_goal]:
            if goal in pdy[anl_ctxt]: # bw jt fw
                anl_prob =   pdy[ctxt][anl_goal]['fw']     \
                           * pdy[anl_ctxt][anl_goal]['bw'] \
                           * pdy[anl_ctxt][goal]['fw']
                lr_words[anl_ctxt] += anl_prob
                rl_words[anl_goal] += anl_prob
                z_paths.append((anl_ctxt, anl_goal))
    # Analogical context words:
    ll_words = defaultdict(float)
    for anl_envr in cdy['bw'][ctxt]:
        for anl_ctxt in cdy['fw'][anl_envr]:
            if '</s>' not in anl_ctxt and goal in pdy[anl_ctxt]:
                anl_prob =   pdy[anl_envr][ctxt]['bw']     \
                           * pdy[anl_envr][anl_ctxt]['fw'] \
                           * pdy[anl_ctxt][goal]['fw']
                ll_words[anl_ctxt] += anl_prob
    # Analogical goal words:
    rr_words = defaultdict(float)
    for anl_goal in cdy['fw'][ctxt]:
        if '</s>' not in anl_goal:
            for anl_envr in cdy['fw'][anl_goal]:
                if goal in cdy['bw'][anl_envr]:
                    anl_prob =   pdy[goal][anl_envr]['fw']     \
                               * pdy[anl_goal][anl_envr]['bw'] \
                               * pdy[ctxt][anl_goal]['bw']
                    rr_words[anl_goal] += anl_prob
    # Best paths:
    substs = defaultdict(float)
    cross_substs = defaultdict(float)
    for l_word, r_word in z_paths:
        l_prob = sum(pdy[l_word][word]['jt'] for word in pdy[l_word])
        r_prob = sum(pdy[word][r_word]['jt'] for word in pdy
                                             if r_word in pdy[word])
        substs[l_word + r_word] +=   (lr_words[l_word] * ll_words[l_word]
                                                       / l_prob) \
                                   * (rl_words[r_word] * rr_words[r_word]
                                                       / r_prob)
        substs[ctxt + r_word]   += rl_words[r_word] * rr_words[r_word] / r_prob
        substs[l_word + goal]   += lr_words[l_word] * ll_words[l_word] / l_prob
        cross_substs[l_word + r_word] +=   (lr_words[l_word] * ll_words[l_word]
                                                             / l_prob) \
                                         * (rl_words[r_word] * rr_words[r_word]
                                                             / r_prob)
    substs = [x for x in substs.items() if x[1] > 0]
    substs.sort(key=lambda x: x[1], reverse=True)
    cross_substs = [x for x in cross_substs.items() if x[1] > 0]
    cross_substs.sort(key=lambda x: x[1], reverse=True)
    return (substs, cross_substs)

# ------------- #
# Trigram model #
# ------------- #

def ctxt_dy3(train):
    cdy = {'fw': defaultdict(lambda: defaultdict(int)),
           'bw': defaultdict(lambda: defaultdict(int))}
    for sentence in train:
        trigrams = ngrams_list(sentence, 3)
        for trigram in trigrams:
            # Record ['the' -> 'king was'] and ['the king' -> 'was']
            for i in range(2):
                cdy['fw'][trigram[:i+1]][trigram[i+1:]] += 1
                cdy['bw'][trigram[i+1:]][trigram[:i+1]] += 1
            # Record ['king' -> 'was']:
            cdy['fw'][trigram[1:2]][trigram[2:]] += 1
            cdy['bw'][trigram[2:]][trigram[1:2]] += 1
    # Convert cdy from defaultdict to dict (dr is direction i.e. 'fw' or 'bw')
    cdy = {dr: {ctxt: dict(cdy[dr][ctxt]) for ctxt in cdy[dr]} for dr in cdy}
    return cdy

def ctxt_dy3(train):
    cdy = {'fw': defaultdict(lambda: defaultdict(int)),
           'bw': defaultdict(lambda: defaultdict(int))}
    for sentence in train:
        trigrams = ngrams_list(sentence, 3)
        for trigram in trigrams:
            # Record ['the' -> 'king was'] and ['the king' -> 'was']
            for i in range(2):
                cdy['fw'][trigram[:i+1]][trigram[i+1:]] += 1
                cdy['bw'][trigram[i+1:]][trigram[:i+1]] += 1
            # Record ['king' -> 'was']:
            cdy['fw'][trigram[1:2]][trigram[2:]] += 1
            cdy['bw'][trigram[2:]][trigram[1:2]] += 1
    # Convert cdy from defaultdict to dict (dr is direction i.e. 'fw' or 'bw')
    cdy = {dr: {ctxt: dict(cdy[dr][ctxt]) for ctxt in cdy[dr]} for dr in cdy}
    return cdy

def prob_dy3(train):
    total_freq = sum(len(sentence) + 1 for sentence in train)
    cdy = ctxt_dy3(train)
    pdy = defaultdict(lambda: defaultdict(dict))
    for ctxt in cdy['fw']:
        ctxt_freq = sum(cdy['fw'][ctxt][goal] for goal in cdy['fw'][ctxt]
                                              if len(goal) == 1)
        for goal in cdy['fw'][ctxt]:
            joint_freq = cdy['fw'][ctxt][goal]
            goal_freq = sum(cdy['bw'][goal][ctxt] for ctxt in cdy['bw'][goal]
                                                  if len(ctxt) == 1)
            probs = {'fw': joint_freq / ctxt_freq,
                     'bw': joint_freq / goal_freq,
                     'jt': joint_freq / total_freq}
            pdy[ctxt][goal] = probs
    pdy = {ctxt: {goal: pdy[ctxt][goal] for goal in pdy[ctxt]} for ctxt in pdy}
    return (cdy, pdy)

def aps3(ctxt, goal, model):
    '''
    # If input is duplet_string, e.g. 'the ; old king'
    ctxt, goal = str2dpl(duplet_string)
    '''
    cdy, pdy = model
    # Middle analogies
    lr_items = defaultdict(float)
    rl_items = defaultdict(float)
    middle_paths = set()
    for anl_goal in cdy['fw'][ctxt]:
        if len(cdy['bw'][anl_goal]) < len(cdy['bw'][goal]):
            for anl_ctxt in cdy['bw'][anl_goal]:
                if goal in cdy['fw'][anl_ctxt]:
                    anl_prob =   pdy[ctxt][anl_goal]['fw']     \
                               * pdy[anl_ctxt][anl_goal]['bw'] \
                               * pdy[anl_ctxt][goal]['fw']
                    lr_items[anl_ctxt] += anl_prob
                    rl_items[anl_goal] += anl_prob
                    middle_paths.add((anl_ctxt, anl_goal))
        else:
            for anl_ctxt in cdy['bw'][goal]:
                if anl_goal in cdy['fw'][anl_ctxt]:
                    anl_prob =   pdy[ctxt][anl_goal]['fw']     \
                               * pdy[anl_ctxt][anl_goal]['bw'] \
                               * pdy[anl_ctxt][goal]['fw']
                    lr_items[anl_ctxt] += anl_prob
                    rl_items[anl_goal] += anl_prob
                    middle_paths.add((anl_ctxt, anl_goal))
    # Left analogies
    ll_items = defaultdict(float)
    for anl_envr in cdy['bw'][ctxt]:
        if len(cdy['fw'][anl_envr]) < len(cdy['bw'][goal]):
            for anl_ctxt in cdy['fw'][anl_envr]:
                if '</s>' in anl_ctxt:
                    continue
                if goal in cdy['fw'][anl_ctxt]:
                    anl_prob =   pdy[anl_envr][ctxt]['bw']     \
                               * pdy[anl_envr][anl_ctxt]['fw'] \
                               * pdy[anl_ctxt][goal]['fw']
                    ll_items[anl_ctxt] += anl_prob
        else:
            for anl_ctxt in cdy['bw'][goal]:
                if '<s>' in anl_ctxt:
                    continue
                if anl_envr in cdy['bw'][anl_ctxt]:
                    anl_prob =   pdy[anl_envr][ctxt]['bw']     \
                               * pdy[anl_envr][anl_ctxt]['fw'] \
                               * pdy[anl_ctxt][goal]['fw']
                    ll_items[anl_ctxt] += anl_prob
    # Right analogies
    rr_items = defaultdict(float)
    for anl_goal in cdy['fw'][ctxt]:
        if '</s>' in anl_goal:
            continue
        if len(cdy['fw'][anl_goal]) < len(cdy['fw'][goal]):
            for anl_envr in cdy['fw'][anl_goal]:
                if goal in cdy['bw'][anl_envr]:
                    anl_prob =   pdy[ctxt][anl_goal]['fw']     \
                               * pdy[anl_goal][anl_envr]['fw'] \
                               * pdy[goal][anl_envr]['bw']
                    rr_items[anl_goal] += anl_prob
        else:
            for anl_envr in cdy['fw'][goal]:
                if anl_goal in cdy['bw'][anl_envr]:
                    anl_prob =   pdy[ctxt][anl_goal]['fw']     \
                               * pdy[anl_goal][anl_envr]['fw'] \
                               * pdy[goal][anl_envr]['bw']
                    rr_items[anl_goal] += anl_prob
    # Best analogies
    substs = defaultdict(float)
    for l_item, r_item in middle_paths:
        # Exclude long paths:
        if len(l_item + r_item) > 2:
            continue
        l_prob = (sum(cdy['fw'][l_item].values()) / 2)
        r_prob = (sum(cdy['bw'][r_item].values()) / 2)
        substs[l_item + r_item] +=   (lr_items[l_item] * ll_items[l_item]) \
                                   * (rl_items[r_item] * rr_items[r_item]) #\
                                   #/ (l_prob * r_prob)
        if len(ctxt) == 1:
            substs[ctxt + r_item]   += (rr_items[r_item] / r_prob) * rl_items[r_item]
        if len(goal) == 1:
            substs[l_item + goal]   += (ll_items[l_item] / l_prob) * lr_items[l_item]
    substs = [x for x in substs.items() if x[1] > 0]
    substs.sort(key=lambda x: x[1], reverse=True)
    return substs

def trig_ps(trigram_string, model):
    trigram = tuple(trigram_string.split())
    cdy, pdy = model
    splits = [(trigram[:i+1], trigram[i+1:] ) for i in range(2)]
    anl_paths = defaultdict(float)
    anl_dy = defaultdict(lambda: defaultdict(float))
    for ctxt, goal in splits:
        if len(ctxt) > 1:
            rec_ctxts = aps3(ctxt[:1], ctxt[1:], model)
        else:
            rec_ctxts = [(ctxt, 1)]
        if len(goal) > 1:
            rec_goals = aps3(goal[:1], goal[1:], model)
        else:
            rec_goals = [(goal, 1)]
        for ctxt_sub, ctxt_score in rec_ctxts:
            for goal_sub, goal_score in rec_goals:
                paths = aps3(ctxt_sub, goal_sub, model)
                for path, path_score in paths:
                    anl_score = path_score * ctxt_score * goal_score
                    anl_paths[path] += anl_score
                    anl_dy[(ctxt, goal)][(ctxt_sub, goal_sub)] += anl_score
    path_dy = sorted(list(anl_paths.items()), key=lambda x: x[1], reverse=True)
    return path_dy

def rec_parse(gram, model, anl_dy=None):
    # Use empty dict as default value for argument `anl_dy`
    if anl_dy == None:
        anl_dy = {}
    # Attempt dynamic lookup
    try:
        return (anl_dy, anl_dy[gram])
    except KeyError:
        pass
    # End recursion when we reach unigrams
    if len(gram) == 1:
        anl_dy[gram] = [((gram, gram), 1)]
        return (anl_dy, [((gram, gram), 1)])
    # Recursive step
    splits = ((gram[:i], gram[i:]) for i in range(1,len(gram)))
    split_anls = {}
    anl_path_dy = defaultdict(float)
    for ctxt, goal in splits:
        split_anls[(ctxt, goal)] = defaultdict(float)
        # Recursive calls
        ctxt_subs = rec_parse(ctxt, model, anl_dy)[1]
        goal_subs = rec_parse(goal, model, anl_dy)[1]
        for ctxt_sub, ctxt_score in ctxt_subs:
            for goal_sub, goal_score in goal_subs:
                paths = aps3(ctxt_sub[0], goal_sub[0], model)[:5]
                for path, path_score in paths:
                    score = path_score #* ctxt_score * goal_score
                    split_anls[(ctxt, goal)][path] += score
                    anl_path_dy[(path, (ctxt, goal))] += score
    anls = sorted(list(anl_path_dy.items()), key=lambda x: x[1], reverse=True)[:5]
    anl_dy[gram] = anls
    return (anl_dy, anls)

def str2dpl(duplet_string):
    duplet_list = duplet_string.split()
    return (tuple(duplet_list[:duplet_list.index(';')]),
            tuple(duplet_list[duplet_list.index(';')+1:]))

def ctxt_dy(corpus, n):
    ngrams = [x for sentence in corpus for x in ngrams_list(sentence, n)]
    ngrams_rev = [tuple(reversed(ngram)) for ngram in ngrams]
    cdy = {}
    cdy['fw'] = ctxt_dy_aux(ngrams, n)
    cdy['bw'] = ctxt_dy_aux(ngrams_rev, n)
    return cdy

def ctxt_dy_aux(ngrams, n):
    # End recursion at unigrams, just return dict with counts
    if n == 1:
        cdy = {ngram[0]: {'#': ngrams.count(ngram)} for ngram in set(ngrams)}
        cdy['#'] = sum(cdy[word]['#'] for word in cdy)
        return cdy
    # Sort tails of ngrams according to head word
    cdy_lists = defaultdict(list)
    for ngram in ngrams:
        cdy_lists[ngram[0]].append(ngram[1:])
    # Recursively compute context dict for each head word
    cdy = {word: ctxt_dy_aux(cdy_lists[word], n-1) for word in cdy_lists}
    cdy['#'] = sum(cdy[word]['#'] for word in cdy)
    return cdy

def fw_count(ngram, cdy):
    rem_dy = cdy['fw']
    for word in ngram:
        try:
            rem_dy = rem_dy[word]
        except:
            return 0
    return rem_dy['#']

def bw_count(ngram, cdy):
    rem_dy = cdy['bw']
    for word in reversed(ngram):
        try:
            rem_dy = rem_dy[word]
        except:
            return 0
    return rem_dy['#']

def fw_look(ngram, cdy):
    rem_dy = cdy['fw']
    for word in ngram:
        rem_dy = rem_dy[word]
    return rem_dy

def fw_nbs(cdy, ngram1, ngram2):
    return fw_nbs_aux(fw_look(ngram1, cdy), fw_look(ngram2, cdy))

def fw_nbs_aux(rem_dy1, rem_dy2, path=()):
    if len(rem_dy1) == 1 or len(rem_dy2) == 1:
        return []
    rem_dys = (rem_dy1, rem_dy2)
    index = len(rem_dy1) <= len(rem_dy2)
    nbs = []
    for word in rem_dys[index]:
        if word != '#' and word in rem_dys[1-index]:
            path += (word,)
            nbs.append(path)
            nbs += fw_nbs_aux(rem_dy1[word], rem_dy2[word], path)
            path = path[:-1]
    return nbs

def prob(dr, ngram1, ngram2, cdy):
    if dr == 'fw':
        return fw_count(ngram1 + ngram2, cdy) / fw_count(ngram1, cdy)
    elif dr == 'bw':
        return fw_count(ngram1 + ngram2, cdy) / bw_count(ngram2, cdy)
    elif dr == 'jt':
        return fw_count(ngram1 + ngram2, cdy) / fw_count((), cdy)