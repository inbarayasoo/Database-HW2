from typing import List, Tuple
from psycopg2 import sql
from datetime import date, datetime


import SimpleTest
import Utility.DBConnector as Connector
from Utility.ReturnValue import ReturnValue
from Utility.Exceptions import DatabaseException
from Business.Customer import Customer, BadCustomer
from Business.Order import Order, BadOrder
from Business.Dish import Dish, BadDish
from Business.OrderDish import OrderDish


# ---------------------------------- CRUD API: ----------------------------------
# Basic database functions


def create_tables() -> None:
    conn = None
    try:
        conn = Connector.DBConnector()
        query = sql.SQL("""CREATE TABLE "Customer"(cust_id INTEGER PRIMARY KEY CHECK(cust_id > 0),  
                        full_name TEXT NOT NULL,
                         phone TEXT NOT NULL,
                         address TEXT NOT NULL CHECK(length(address) >= 3));

                         CREATE TABLE "Order"(
                            order_id INTEGER PRIMARY KEY CHECK(order_id > 0),
                            date TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL);
        
                        CREATE TABLE "Dish"(
                             dish_id INTEGER PRIMARY KEY CHECK(dish_id > 0),
                             name TEXT NOT NULL CHECK(length(TRIM(name)) >= 3),
                             price DECIMAL NOT NULL CHECK(price > 0),
                             is_active BOOLEAN NOT NULL);
                     
                        CREATE TABLE "Customer_Orders"(
                            cust_id INTEGER,
                            order_id INTEGER PRIMARY KEY,
                            FOREIGN KEY (cust_id) REFERENCES "Customer"(cust_id) ON DELETE CASCADE,
                            FOREIGN KEY (order_id) REFERENCES "Order"(order_id) ON DELETE CASCADE,
                            CHECK(order_id > 0),
                            CHECK(cust_id > 0));
                            
                     
                        CREATE TABLE "Dishes_in_Order"(
                            order_id INTEGER , 
                            dish_id INTEGER ,
                            amount INTEGER,
                            price DECIMAL,
                            FOREIGN KEY (order_id) REFERENCES "Order"(order_id) ON DELETE CASCADE,
                            FOREIGN KEY (dish_id) REFERENCES "Dish"(dish_id),
                            CONSTRAINT PK_order_dish PRIMARY KEY (order_id,dish_id),
                            CHECK(order_id > 0),
                            CHECK(dish_id > 0),
                            CHECK(amount > 0));
                            
                        CREATE TABLE "Likes"(
                            cust_id INTEGER,
                            dish_id INTEGER,
                            FOREIGN KEY (cust_id) REFERENCES "Customer"(cust_id) ON DELETE CASCADE,
                            FOREIGN KEY (dish_id) REFERENCES "Dish"(dish_id),
                            CONSTRAINT PK_cust_dish PRIMARY KEY (cust_id,dish_id),
                            CHECK(cust_id > 0),
                            CHECK(dish_id > 0));
                            
                        CREATE VIEW "OrderTotalPrice" AS
                            SELECT co.order_id, COALESCE(SUM(dio.price * dio.amount), 0) AS total_price
                            FROM "Order" co
                            JOIN "Dishes_in_Order" AS dio ON co.order_id = dio.order_id
                            GROUP BY co.order_id;
                        
                        CREATE VIEW "MostLikedDishes" AS
                            SELECT dish_id, COUNT(*) AS likes_count
                            FROM "Likes"
                            GROUP BY dish_id;
                            
                        CREATE VIEW "MostPurchasedDish" AS
                            SELECT dio.dish_id, SUM(dio.amount) as total_sum
                            FROM "Dishes_in_Order" dio
                            JOIN "Order" o ON dio.order_id = o.order_id
                            WHERE o.order_id IN (SELECT order_id FROM "Dishes_in_Order")
                            GROUP BY dio.dish_id;
                        """)
        conn.execute(query)

    except DatabaseException.ConnectionInvalid as e:
        print(e)
    except DatabaseException.NOT_NULL_VIOLATION as e:
        print(e)
    except DatabaseException.CHECK_VIOLATION as e:
        print(e)
    except DatabaseException.UNIQUE_VIOLATION as e:
        print(e)
    except DatabaseException.FOREIGN_KEY_VIOLATION as e:
        print(e)
    except Exception as e:
        print(e)
    finally:
        if conn:
            conn.close()


def check_add_query(query) -> tuple:
    conn = None
    affected_rows = 0
    result = ReturnValue.OK
    try:
        conn = Connector.DBConnector()
        affected_rows, _ = conn.execute(query)
    except DatabaseException.ConnectionInvalid:
        result = ReturnValue.ERROR
    except DatabaseException.NOT_NULL_VIOLATION:
        result = ReturnValue.BAD_PARAMS
    except DatabaseException.CHECK_VIOLATION:
        result = ReturnValue.BAD_PARAMS
    except DatabaseException.UNIQUE_VIOLATION:
        result = ReturnValue.ALREADY_EXISTS
    except DatabaseException.FOREIGN_KEY_VIOLATION:
        result = ReturnValue.NOT_EXISTS
    except Exception:
        result = ReturnValue.ERROR
    finally:
        if conn is not None:
            conn.close()
    return result,affected_rows



def check_aux_query(query) -> ReturnValue:
    conn = None
    res = ReturnValue.OK
    try:
        conn = Connector.DBConnector()
        rows_effected, _ = conn.execute(query)

        if (rows_effected == 0):
            res = ReturnValue.NOT_EXISTS

    except DatabaseException.ConnectionInvalid as e:
        res = ReturnValue.ERROR
    except DatabaseException.NOT_NULL_VIOLATION as e:
        res = ReturnValue.BAD_PARAMS
    except DatabaseException.CHECK_VIOLATION as e:
        res = ReturnValue.BAD_PARAMS
    except DatabaseException.UNIQUE_VIOLATION as e:
        res = ReturnValue.ALREADY_EXISTS
    except DatabaseException.FOREIGN_KEY_VIOLATION as e:
        res = ReturnValue.NOT_EXISTS
    except Exception as e:
        res = ReturnValue.ERROR
    finally:
        conn.close()
    return res


def clear_tables() -> None:
    conn = None
    try:
        conn = Connector.DBConnector()
        conn.execute("""
                        DELETE FROM "Customer_Orders";
                        DELETE FROM "Dishes_in_Order";
                        DELETE FROM "Likes";
                        DELETE FROM "Customer";
                        DELETE FROM "Order";
                        DELETE FROM "Dish";
                        """)

    except DatabaseException.ConnectionInvalid as e:
        print(e)
    except DatabaseException.NOT_NULL_VIOLATION as e:
        print(e)
    except DatabaseException.CHECK_VIOLATION as e:
        print(e)
    except DatabaseException.UNIQUE_VIOLATION as e:
        print(e)
    except DatabaseException.FOREIGN_KEY_VIOLATION as e:
        print(e)
    except Exception as e:
        print(e)
    finally:
        if conn:
            conn.close()


def drop_tables() -> None:
    conn = None
    try:
        conn = Connector.DBConnector()
        conn.execute("""DROP TABLE IF EXISTS "Customer" CASCADE;
                    DROP TABLE IF EXISTS "Order" CASCADE;
                    DROP TABLE IF EXISTS "Dish" CASCADE;
                    DROP TABLE IF EXISTS "Customer_Orders" CASCADE;
                    DROP TABLE IF EXISTS "Dishes_in_Order" CASCADE;
                    DROP TABLE IF EXISTS "Likes" CASCADE;
                    DROP VIEW IF EXISTS "OrderDishesView" CASCADE;
                    DROP VIEW IF EXISTS "OrderTotalPrice" CASCADE;""")

    except DatabaseException.ConnectionInvalid as e:
        print(e)
    except DatabaseException.NOT_NULL_VIOLATION as e:
        print(e)
    except DatabaseException.CHECK_VIOLATION as e:
        print(e)
    except DatabaseException.UNIQUE_VIOLATION as e:
        print(e)
    except DatabaseException.FOREIGN_KEY_VIOLATION as e:
        print(e)
    except Exception as e:
        print(e)
    finally:
        if conn:
            conn.close()


# CRUD API

def add_customer(customer: Customer) -> ReturnValue:
    query = sql.SQL("""INSERT INTO "Customer"(cust_id,full_name,phone,address) 
    VALUES({cust_id}, {full_name},{phone},{address})""").format(cust_id=sql.Literal(customer.get_cust_id()),
                                                                full_name=sql.Literal(customer.get_full_name()),
                                                                phone=sql.Literal(customer.get_phone()),
                                                                address=sql.Literal(customer.get_address()))
    result, affected_rows = check_add_query(query)
    return result


def get_customer(customer_id: int) -> Customer:
    if customer_id is None:
        return ReturnValue.BAD_PARAMS
    if customer_id <= 0:
        return ReturnValue.BAD_PARAMS
    conn = None
    try:
        query = sql.SQL("""SELECT * FROM "Customer" WHERE cust_id = {id}""").format(id=sql.Literal(customer_id))
        conn = Connector.DBConnector()
        result = conn.execute(query)

        if result[0] == 0:
            customer = BadCustomer()
        else:
            customer = Customer(result[1][0]['cust_id'],
                                result[1][0]['full_name'], result[1][0]['phone'], result[1][0]['address'])

    except Exception:
        customer = BadCustomer()
    finally:
        conn.close()
    return customer


def delete_customer(customer_id: int) -> ReturnValue:
    query = sql.SQL("""DELETE FROM "Customer" WHERE cust_id = {id}""").format(id=sql.Literal(customer_id))
    return check_aux_query(query)


def add_order(order: Order) -> ReturnValue:
    if order.get_order_id() is None or order.get_order_id() <= 0:
        return ReturnValue.BAD_PARAMS
    query = sql.SQL("""INSERT INTO "Order"(order_id,date) 
        VALUES({order_id}, {date})""").format(order_id=sql.Literal(order.get_order_id()),
                                              date=sql.Literal(order.get_datetime()))
    result, affected_rows = check_add_query(query)
    return result


def get_order(order_id: int) -> Order:
    conn = None
    try:
        query = sql.SQL("""SELECT * FROM "Order" WHERE order_id = {id}""").format(id=sql.Literal(order_id))
        conn = Connector.DBConnector()
        result = conn.execute(query)
        if result[0] == 0:
            order = BadOrder()
        else:
            order = Order(result[1][0]['order_id'],
                          result[1][0]['date'])

    except Exception:
        order = BadOrder()
    finally:
        conn.close()
    return order


def delete_order(order_id: int) -> ReturnValue:
    query = sql.SQL("""DELETE FROM "Order" WHERE order_id = {id}""").format(id=sql.Literal(order_id))
    return check_aux_query(query)


def add_dish(dish: Dish) -> ReturnValue:
    query = sql.SQL("""INSERT INTO "Dish"(dish_id,name,price,is_active) 
           VALUES({dish_id},{name},{price}, {is_active})""").format(dish_id=sql.Literal(dish.get_dish_id()),
                                                                    name=sql.Literal(dish.get_name()),
                                                                    price=sql.Literal(dish.get_price()),
                                                                    is_active=sql.Literal(dish.get_is_active()))
    result, affected_rows = check_add_query(query)
    return result


def get_dish(dish_id: int) -> Dish:
    conn = None
    try:
        query = sql.SQL("""SELECT * FROM "Dish" WHERE dish_id = {dish_id}""").format(dish_id=sql.Literal(dish_id))
        conn = Connector.DBConnector()
        result = conn.execute(query)
        if result[0] == 0:
            dish = BadDish()
        else:
            dish = Dish(result[1][0]['dish_id'],
                        result[1][0]['name'],
                        result[1][0]['price'],
                        result[1][0]['is_active'])

    except Exception:
        dish = BadDish()
    finally:
        conn.close()
    return dish


def update_dish_price(dish_id: int, price: float) -> ReturnValue:
    query = sql.SQL("""UPDATE "Dish" SET price = {price} WHERE dish_id = {dish_id} AND is_active = True""").format(
        price=sql.Literal(price),
        dish_id=sql.Literal(
            dish_id))

    return check_aux_query(query)


def update_dish_active_status(dish_id: int, is_active: bool) -> ReturnValue:
    query = sql.SQL("""UPDATE "Dish" SET is_active = {active} WHERE dish_id = {dish_id}""").format(
        active=sql.Literal(is_active),
        dish_id=sql.Literal(
            dish_id))

    return check_aux_query(query)


def customer_placed_order(customer_id: int, order_id: int) -> ReturnValue:
    query = sql.SQL("""INSERT INTO "Customer_Orders"(cust_id,order_id) 
        VALUES({cust_id}, {order_id})""").format(cust_id=sql.Literal(customer_id),
                                                 order_id=sql.Literal(order_id))
    result, rows_affected = check_add_query(query)
    if result == ReturnValue.BAD_PARAMS:
        return ReturnValue.NOT_EXISTS
    return result


def get_customer_that_placed_order(order_id: int) -> Customer:
    conn = None
    try:
        query = sql.SQL("""SELECT co.cust_id, full_name, phone, address FROM "Customer_Orders" AS co 
        JOIN "Customer" AS c ON c.cust_id = co.cust_id
        WHERE co.order_id = {order_id}""").format(order_id=sql.Literal(order_id))

        conn = Connector.DBConnector()
        result = conn.execute(query)
        if result[0] == 0:
            customer = BadCustomer()
        else:
            customer = Customer(result[1][0]['cust_id'],
                                result[1][0]['full_name'], result[1][0]['phone'], result[1][0]['address'])

    except Exception:
        customer = BadCustomer()
    finally:
        conn.close()
    return customer


def order_contains_dish(order_id: int, dish_id: int, amount: int) -> ReturnValue:
    if amount < 0:
        return ReturnValue.BAD_PARAMS

    query = sql.SQL("""INSERT INTO "Dishes_in_Order"(order_id, dish_id,amount, price) 
                 VALUES({order_id}, 
                 (SELECT dish_id FROM "Dish" WHERE dish_id = {dish_id} AND is_active = True), {amount},  
                 (SELECT price FROM "Dish" WHERE dish_id = {dish_id} AND is_active = True))
                 """).format(order_id=sql.Literal(order_id),
                             dish_id=sql.Literal(dish_id),
                             amount=sql.Literal(amount))
    result,rows_affected = check_add_query(query)
    if result == ReturnValue.BAD_PARAMS:
        return ReturnValue.NOT_EXISTS
    return result


def order_does_not_contain_dish(order_id: int, dish_id: int) -> ReturnValue:
    query = sql.SQL("""DELETE FROM "Dishes_in_Order" WHERE 
                    order_id = {order_id} AND dish_id = {dish_id} """).format(order_id=sql.Literal(order_id),
                                                                              dish_id=sql.Literal(dish_id))
    return check_aux_query(query)


def get_all_order_items(order_id: int) -> List[OrderDish]:
    conn = None
    try:
        query = sql.SQL("""SELECT dio.dish_id,dio.amount, dio.price FROM "Dishes_in_Order" AS dio
         JOIN "Dish" AS d ON d.dish_id =  dio.dish_id
         WHERE order_id = {order_id} ORDER BY dish_id ASC""").format(
            order_id=sql.Literal(order_id))
        conn = Connector.DBConnector()
        result = conn.execute(query)
        list = []
        if result[0] == 0:
            list = []  # empty list
        else:
            rows = result[1]
            for row in rows:
                dish = OrderDish(
                    dish_id=row['dish_id'],
                    amount=row['amount'],
                    price=row['price'],
                )
                list.append(dish)
    except Exception as e:
        list = []
    finally:
        conn.close()
    return list


def customer_likes_dish(cust_id: int, dish_id: int) -> ReturnValue:
    query = sql.SQL("""INSERT INTO "Likes"(cust_id,dish_id) 
        VALUES({cust_id}, {dish_id})""").format(cust_id=sql.Literal(cust_id),
                                                dish_id=sql.Literal(dish_id))
    result, rows_affected = check_add_query(query)
    if result == ReturnValue.BAD_PARAMS:
        return ReturnValue.NOT_EXISTS
    return result


def customer_dislike_dish(cust_id: int, dish_id: int) -> ReturnValue:
    query = sql.SQL("""DELETE FROM "Likes" 
                    WHERE cust_id = {cust_id} AND dish_id = {dish_id}""").format(cust_id=sql.Literal(cust_id),
                                                                                 dish_id=sql.Literal(dish_id))
    result, affected_rows = check_add_query(query)
    if result == ReturnValue.OK:
        if affected_rows == 0:
            return ReturnValue.NOT_EXISTS
        return ReturnValue.OK
    return result


def get_all_customer_likes(cust_id: int) -> List[Dish]:

    conn = None
    try:
        query = sql.SQL("""SELECT l.dish_id,d.name, d.price, d.is_active FROM "Likes" AS l
                        JOIN "Dish" AS d ON d.dish_id = l.dish_id    
                        WHERE cust_id = {cust_id} ORDER BY l.dish_id ASC""").format(cust_id=sql.Literal(cust_id))

        conn = Connector.DBConnector()
        result = conn.execute(query)
        list = []
        if result[0] == 0:
            list = []  # empty list
        else:
            rows = result[1]
            for row in rows:
                dish = Dish(
                    dish_id=row['dish_id'],
                    name=row['name'],
                    price=row['price'],
                    is_active=row['is_active']
                )
                list.append(dish)
    except Exception as e:
        list = []
    finally:
        conn.close()
    return list


# ---------------------------------- BASIC API: ----------------------------------

# Basic API

def get_order_total_price(order_id: int) -> float:
    conn = None
    try:
        query = sql.SQL("""SELECT total_price FROM "OrderTotalPrice"
                        WHERE order_id = {order_id}""").format(order_id=sql.Literal(order_id))

        conn = Connector.DBConnector()
        result = conn.execute(query)
        if result[0] == 0:
            total_price = 0.0
        else:
            total_price = result[1][0]['total_price']

    except Exception:
        total_price = 0.0
    finally:
        conn.close()
    return float(total_price)


def get_max_amount_of_money_cust_spent(cust_id: int) -> float:
    conn = None
    try:
        query = sql.SQL("""SELECT MAX(total_price) AS max FROM "OrderTotalPrice" AS otp
                            JOIN "Customer_Orders" AS co ON co.order_id = otp.order_id
                            WHERE co.cust_id = {cust_id}""").format(cust_id=sql.Literal(cust_id))
        conn = Connector.DBConnector()
        result = conn.execute(query)
        if result[1][0]['max'] is None:
            max_price = 0.0
        else:
            max_price = result[1][0]['max']

    except Exception as e:
        max_price = 0.0
    finally:
        conn.close()
    return float(max_price)


def get_most_expensive_anonymous_order() -> Order:
    conn = None
    query = sql.SQL(""" SELECT o.order_id, o.date, 
                            COALESCE(SUM(dio.price * dio.amount), 0) AS total_price
                        FROM "Order" o
                        LEFT JOIN "Customer_Orders" co ON o.order_id = co.order_id
                        LEFT JOIN "Dishes_in_Order" dio ON o.order_id = dio.order_id
                        WHERE co.order_id IS NULL
                        GROUP BY o.order_id
                        ORDER BY total_price DESC, o.order_id ASC
                        LIMIT 1;""")
    conn = Connector.DBConnector()
    result = conn.execute(query)
    order_result = Order(result[1][0]['order_id'], result[1][0]['date'])
    conn.close()
    return order_result


def is_most_liked_dish_equal_to_most_purchased() -> bool:
    conn = None
    query = sql.SQL("""
        SELECT EXISTS (
        SELECT equal_id
        FROM (
            SELECT ld.dish_id AS equal_id
            FROM "MostLikedDishes" AS ld
            ORDER BY ld.likes_count DESC, ld.dish_id ASC
            LIMIT 1
        ) AS most_liked
        JOIN (
            SELECT pd.dish_id
            FROM "MostPurchasedDish" AS pd
            ORDER BY pd.total_sum DESC ,pd.dish_id ASC
            LIMIT 1
        ) AS most_purchased ON most_purchased.dish_id = most_liked.equal_id
    ) AS is_equal;""")
    try:
        conn = Connector.DBConnector()
        result = conn.execute(query)

        return result[1][0]['is_equal']
    except Exception as e:
        return False
    finally:
        conn.close()


# ---------------------------------- ADVANCED API: ----------------------------------

# Advanced API


def get_customers_ordered_top_5_dishes() -> List[int]:
    # todo - check what if there are no 5 liked dishes
    conn = None
    try:
        query = sql.SQL("""SELECT cust_id 
    FROM (
        "Customer_Orders" AS co
        JOIN "Dishes_in_Order" AS dio ON co.order_id = dio.order_id
    ) AS l
    WHERE dish_id IN (
        SELECT d.dish_id
        FROM 
            "MostLikedDishes" AS mld
        FULL OUTER JOIN 
            (SELECT dish_id FROM "Dish") AS d
        ON mld.dish_id = d.dish_id
        ORDER BY mld.likes_count DESC, d.dish_id ASC
        LIMIT 5
    )
    GROUP BY cust_id 
    HAVING COUNT(DISTINCT dish_id) = (
        SELECT COUNT(*) 
        FROM (
            SELECT d.dish_id
            FROM 
                "MostLikedDishes" AS mld
            FULL OUTER JOIN 
                (SELECT dish_id FROM "Dish") AS d
            ON mld.dish_id = d.dish_id
            ORDER BY mld.likes_count DESC, d.dish_id ASC
            LIMIT 5
        ) AS subquery
    )
    ORDER BY cust_id ASC;""")

        conn = Connector.DBConnector()
        result = conn.execute(query)
        list = []
        if result[0] == 0:
            list = []  # empty list
        else:
            rows = result[1]
            for row in rows:
                list.append(row['cust_id'])

    except Exception:
        list = []
    finally:
        conn.close()
    return list


def get_non_worth_price_increase() -> List[int]:
    conn = None
    try:
        query = sql.SQL("""SELECT cp.dish_id
                            FROM (SELECT d.dish_id, d.price AS current_price,
                                         AVG(dio.amount) * d.price AS current_profit
                                  FROM "Dish" AS d
                                  JOIN "Dishes_in_Order" AS dio ON d.dish_id = dio.dish_id
                                  WHERE d.is_active = TRUE AND dio.price = d.price
                                  GROUP BY d.dish_id, d.price) AS cp
                             
                            JOIN (SELECT dish_id, MAX(previous_profit) AS max_previous_profit
                                  FROM (SELECT dio.dish_id, dio.price AS previous_price,
                                               AVG(dio.amount) * dio.price AS previous_profit
                                        FROM "Dishes_in_Order" AS dio
                                        WHERE dio.price < (SELECT d.price FROM "Dish" AS d WHERE d.dish_id = dio.dish_id)
                                        GROUP BY dio.dish_id, dio.price)
                                  GROUP BY dish_id) AS mpp ON cp.dish_id = mpp.dish_id
                            WHERE cp.current_profit < mpp.max_previous_profit
                            ORDER BY cp.dish_id ASC;""")
        conn = Connector.DBConnector()
        result = conn.execute(query)
        list = []
        if result[0] == 0:
            list = []  # empty list
        else:
            rows = result[1]
            for row in rows:
                list.append(row['dish_id'])

    except Exception as e:
        list = []
    finally:
        conn.close()
    return list


def get_total_profit_per_month(year: int) -> List[Tuple[int, float]]:
    conn = None
    try:
        query = sql.SQL("""
            SELECT 
                EXTRACT(MONTH FROM o.date) as month,
                COALESCE(SUM(od.amount * od.price), 0) as profit
            FROM 
                "Order" o
            LEFT JOIN 
                "Dishes_in_Order" od ON o.order_id = od.order_id
            WHERE 
                EXTRACT(YEAR FROM o.date) = {year}
            GROUP BY 
                EXTRACT(MONTH FROM o.date)
            ORDER BY 
                EXTRACT(MONTH FROM o.date) DESC;
        """).format(year=sql.Literal(year))
        conn = Connector.DBConnector()
        result = conn.execute(query)
        list = []
        if result[0] == 0:
            list = []  # empty list
        else:
            rows = result[1]
            profit_dict = {i: 0.0 for i in range(1, 13)}  # Initialize all months with 0 profit
            for row in rows:
                month = int(float(row['month']))
                profit = float(row['profit'])
                profit_dict[month] = profit

            list = [(month, profit_dict[month]) for month in range(12, 0, -1)]

    except Exception as e:
        list = []
    finally:
        conn.close()

    return list


def get_potential_dish_recommendations(cust_id: int) -> List[int]:
    conn = None
    try:
        query = sql.SQL("""
            SELECT DISTINCT d.dish_id
            FROM "Dish" d
            JOIN "Likes" cl ON d.dish_id = cl.dish_id
            JOIN (
                SELECT c2.cust_id
                FROM "Customer" c2
                JOIN "Likes" cl2 ON c2.cust_id = cl2.cust_id
                JOIN "Likes" cl3 ON cl2.dish_id = cl3.dish_id
                WHERE cl3.cust_id = {cust_id}
                GROUP BY c2.cust_id
                HAVING COUNT(DISTINCT cl2.dish_id) >= 3
            ) similar_customers ON cl.cust_id = similar_customers.cust_id
            WHERE d.dish_id NOT IN (
                SELECT dish_id
                FROM "Likes"
                WHERE cust_id = {cust_id}
            )
            ORDER BY d.dish_id ASC;
        """).format(cust_id=sql.Literal(cust_id))
        conn = Connector.DBConnector()
        result = conn.execute(query)
        list = []
        if result[0] == 0:
            list = []  # empty list
        else:
            rows = result[1]
            for row in rows:
                list.append(row['dish_id'])

    except Exception as e:
        list = []
    finally:
        conn.close()
    return list


if __name__ == '__main__':
    None
