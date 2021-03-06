import logging

from aleph.core import get_graph
from aleph.model import Entity
from aleph.graph.schema import EntityNode, AKA
from aleph.graph.collections import add_to_collections
from aleph.graph.converter import fingerprint
from aleph.graph.util import delete_orphan_nodes

log = logging.getLogger(__name__)


def load_entities():
    graph = get_graph()
    if graph is None:
        return
    tx = graph.begin()
    q = Entity.all()
    q = q.filter(Entity.state == Entity.STATE_ACTIVE)
    for i, entity in enumerate(q):
        load_entity(tx, entity)
        if i > 0 and i % 10000 == 0:
            tx.commit()
            tx = graph.begin()
    tx.commit()


def load_entity(tx, entity):
    if tx is None:
        return
    if entity.state != Entity.STATE_ACTIVE:
        return remove_entity(tx, entity.id)
    log.info("Graph node [%s]: %s", entity.id, entity.name)
    fp = fingerprint(entity.name)
    node = EntityNode.get_cache(tx, fp)
    if node is not None:
        return node

    country_code = entity.jurisdiction_code
    if country_code is not None:
        country_code = country_code.upper()
    node = EntityNode.merge(tx, name=entity.name,
                            fingerprint=fp,
                            alephSchema=entity.type,
                            alephState=entity.state,
                            alephEntity=entity.id)
    add_to_collections(tx, node, entity.collections,
                       alephEntity=entity.id)

    seen = set([fp])
    for other_name in entity.other_names:
        fp = fingerprint(other_name.display_name)
        if fp in seen or fingerprint is None:
            continue
        seen.add(fp)

        alias = EntityNode.merge(tx, name=other_name.display_name,
                                 fingerprint=fp,
                                 alephEntity=entity.id,
                                 alephSchema=entity.type,
                                 isAlias=True)
        AKA.merge(tx, node, alias, alephEntity=entity.id)
        add_to_collections(tx, alias, entity.collections,
                           alephEntity=entity.id)

    # TODO contact details, addresses
    return node


def remove_entity(tx, entity_id):
    if tx is None:
        return
    query = "MATCH ()-[r {alephEntity: {id}}]-() DELETE r;"
    tx.run(query, id=entity_id)
    delete_orphan_nodes(tx)
