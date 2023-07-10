from operator import attrgetter

from sqlalchemy.dialects.postgresql import insert


async def upsert_many(session, table, values, index_elements: list[str], set_: list[str]):
    """
    Upserts multiple rows into the specified table using the given session.

    Args:
        session: The session object to use for executing the upsert operation.
        table: The table to upsert the values into.
        values: A list of dictionaries representing the values to be upserted.
        index_elements: A list of column names that make up the unique index or constraint used for upserting.
        set_: A list of column names to be updated in case of conflict.

    Raises:
        Any exceptions raised by the underlying execution of the upsert operation.

    Example usage:
        session = get_session()
        table = "my_table"
        values = [
            {"id": 1, "name": "John"},
            {"id": 2, "name": "Jane"},
            ...
        ]
        index_elements = ["id"]
        set_ = ["name"]

        await upsert_many(session, table, values, index_elements, set_)
    """
    if values:
        insert_stmt = insert(table).values()
        set_ = {
            column: attrgetter(column)(insert_stmt.excluded)
            for column in set_
        }
        await session.execute(
            insert_stmt.on_conflict_do_update(
                index_elements=index_elements,
                set_=set_
            ),
            values,
        )


def _get_non_index_columns(table, index_elements: set[str]) -> list[str]:
    result = []
    for column in table.c:
        if column.name not in index_elements:
            result.append(column.name)
    return result


async def upsert_many_by_index(session, table, values, index_elements: list[str]):
    await upsert_many(session, table, values, index_elements, _get_non_index_columns(table, set(index_elements)))
