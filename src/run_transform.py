import os
import json
from copy import deepcopy
from typing import Dict, List, Tuple
import UDLib as udlib

CONLLU_PATH = '../conllu'
OUT_PATH = '../conllu-processed'
SNACS_PATH = '../snacs-output/ewt'
ADVMOD_TAGS = {
    'Locus',
    'Time',
    'EndTime',
    'Goal',
    'Source',
    'Purpose',
    'Duration',
    'Circumstance',
    'ComparisonRef',
    'Manner',
    'Extent'
}


def get_annotations(path: str) -> List[Dict[str, List[str]]]:
    result = []
    with open(path, 'r', encoding='utf-8') as inp:
        for line in inp:
            result.append(json.loads(line))
    return result


def get_obliques_with_types(
        t: udlib.UDTree,
        annotation: Dict[str, List[str]]) -> List[Tuple[str]]:
    assert len(t.keys) == len(annotation['tokens'])
    tag_dict = dict(zip(t.keys, annotation['tags']))
    result = []
    # DFS on the tree. Get the real root
    for edge in t.graph['0']:
        root = edge.head
    stack = [root]
    while stack:
        current_node = stack.pop()
        if t.nodes[current_node].DEPREL.split(':')[0] == 'obl':
            # Find the first case child and retrieve its annotation
            for edge in t.graph[current_node]:
                if edge.directionality == 'down':
                    child = edge.head
                    if t.nodes[child].DEPREL.split(':')[0] == 'case':
                        result.append((t.nodes[child].FORM + ' ' + t.nodes[current_node].FORM,
                                       tag_dict[child]))
                        break
            else:
                result.append((t.nodes[current_node].FORM, 'caseless'))
        for edge in t.graph[current_node]:
            if edge.directionality == 'down':
                stack.append(edge.head)
    return result


def transform_obl(t: udlib.UDTree,
                  annotation: Dict[str, List[str]]) -> udlib.UDTree:
    assert len(t.keys) == len(annotation['tokens'])
    tag_dict = dict(zip(t.keys, annotation['tags']))
    result = deepcopy(t)
    # Get the real root
    for edge in t.graph['0']:
        root = edge.head
    # DFS on the tree
    stack = [root]
    while stack:
        current_node = stack.pop()
        if t.nodes[current_node].DEPREL.split(':')[0] == 'obl':
            # Find the first _case_ child and retrieve its annotation
            for edge in t.graph[current_node]:
                if edge.directionality == 'down':
                    child = edge.head
                    if t.nodes[child].DEPREL.split(':')[0] == 'case':
                        tag = tag_dict[child].split('|')[0].split('.')[-1]
                        break
            else:
                tag = 'caseless'
            if tag in ADVMOD_TAGS:
                result.nodes[current_node].DEPREL = 'advmod'
            else:
                result.nodes[current_node].DEPREL = 'iobj'
        for edge in t.graph[current_node]:
            if edge.directionality == 'down':
                stack.append(edge.head)
    return result


def process_file(part: str):
    trees = udlib.conllu2trees(
        os.path.join(CONLLU_PATH, f'en_ewt-ud-{part}.conllu'))
    annotations = get_annotations(os.path.join(SNACS_PATH, part))
    with open(
        os.path.join(OUT_PATH, f'en_ewt-ud-{part}.conllu'), 
        'w', 
        encoding='utf-8'
    ) as out:
        for tree, annotation in zip(trees, annotations):
            print(transform_obl(tree, annotation), file=out)
            print('', file=out)


if __name__ == '__main__':
    for part in ['train', 'dev', 'test']:
        process_file(part)