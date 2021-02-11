import os
import json
from copy import deepcopy
from typing import Dict, List, Tuple
import UDLib as udlib

CONLLU_PATH = 'conllu'
SNACS_PATH = 'snacs-output'
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


def get_obliques_with_types(
        t: udlib.UDTree,
        annotation: Dict[str, List[str]]) -> List[Tuple[str]]:
    assert len(t.keys) == len(annotation['tokens'])
    tag_dict = dict(zip(t.keys, annotation['tags']))
    result = []
    # Get the real root
    for edge in t.graph['0']:
        root = edge.head
    # DFS on the tree
    stack = [root]
    while stack:
        current_node = stack.pop()
        if t.nodes[current_node].DEPREL == 'obl':
            # Find the first _case_ child and retrieve its annotation
            for edge in t.graph[current_node]:
                if edge.directionality == 'down':
                    child = edge.head
                    if t.nodes[child].DEPREL == 'case':
                        result.append((t.nodes[child].FORM + ' ' + t.nodes[current_node].FORM,
                                       tag_dict[child]))
                        break
            else:
                result.append((t.nodes[current_node].FORM, 'caseless obl'))
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
        if t.nodes[current_node].DEPREL == 'obl':
            # Find the first _case_ child and retrieve its annotation
            for edge in t.graph[current_node]:
                if edge.directionality == 'down':
                    child = edge.head
                    if t.nodes[child].DEPREL == 'case':
                        tag = tag_dict[child].split('|')[0].split('.')[-1]
            else:
                tag = 'caseless'
            if tag == 'caseless':
                result.nodes[current_node].DEPREL = 'orphan'
            elif tag in ADVMOD_TAGS:
                result.nodes[current_node].DEPREL = 'advmod'
            else:
                result.nodes[current_node].DEPREL = 'iobj'
            for edge in t.graph[current_node]:
                if edge.directionality == 'down':
                    stack.append(edge.head)
    return result


def get_annotations(path: str) -> List[Dict[str, List[str]]]:
    result = []
    with open(path, 'r', encoding='utf-8') as inp:
        for line in inp:
            result.append(json.loads(line))
    return result
