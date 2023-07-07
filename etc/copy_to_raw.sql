truncate raw.game cascade; 
INSERT INTO raw.game (app_id, name)
SELECT app_id, name
FROM public.game
where public.game.app_id = 730;

truncate raw.market_item cascade; 
INSERT INTO raw.market_item (app_id, market_hash_name, market_fee, market_marketable_restriction, market_tradable_restriction, commodity)
SELECT app_id, market_hash_name, market_fee, market_marketable_restriction, market_tradable_restriction, commodity
FROM public.market_item
where public.market_item.app_id = 730;

truncate raw.market_item_orders cascade; 
INSERT INTO raw.market_item_orders (app_id, market_hash_name, timestamp, dump)
SELECT app_id, market_hash_name, timestamp, dump
FROM public.market_item_orders
where public.market_item_orders.app_id = 730;

truncate raw.market_item_sell_history cascade; 
INSERT INTO raw.market_item_sell_history (app_id, market_hash_name, timestamp, history)
SELECT app_id, market_hash_name, timestamp, history
FROM public.market_item_sell_history
where public.market_item_sell_history.app_id = 730;