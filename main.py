import sqlite3
from datetime import date
from decimal import *
from functools import partial
from tkinter import *
from tkinter import messagebox
from tkinter.messagebox import showerror
from tkinter.ttk import Combobox

from tkcalendar import DateEntry


def get_tables():
    conn = sqlite3.connect('dictionary.db')
    cursor = conn.cursor()
    query = """SELECT name FROM main.sqlite_master
              WHERE type ='table' AND name NOT LIKE 'sqlite_%' AND name <> 'fks_table';"""
    cursor.execute(query, ())
    tables = cursor.fetchall()
    table_names = []
    for table in tables:
        table_names.append(table[0])
    for table_name in table_names:
        query = "PRAGMA table_info(" + table_name + ");"
        cursor.execute(query)
        result = cursor.fetchall()
        i = tables.index((table_name,))
        for res in result:
            tables[i] += (res[1], res[2])
    cursor.close()
    conn.close()

    return tables, table_names


def get_from_table(table_name, order_by_col=0, sort_type=0):
    tables_info, table_names = get_tables()
    if table_name in table_names:
        table_info = tables_info[table_names.index(table_name)]
    else:
        return [], []
    columns = []
    conn = sqlite3.connect('dictionary.db')
    cursor = conn.cursor()
    fks = get_foreign_keys(table_name)
    if not fks:
        for i in range(3, len(table_info) - 3):
            if i % 2:
                columns.append(table_info[i])
        query = "SELECT "
        for i in range(len(columns) - 1):
            query += columns[i] + ', '
        query += columns[-1] + " from " + table_name + " where deleted=0"
        if order_by_col:
            query += ' order by ' + order_by_col + ' ' + sort_type + ';'
        else:
            query += ';'

        cursor.execute(query, ())
        result = cursor.fetchall()
    else:
        fks = fks[0]
        for i in range(5, len(table_info) - 3):
            if i % 2:
                columns.append(table_info[i])
        query = "SELECT "
        for i in range(len(columns)):
            query += table_name + "." + columns[i] + ', '
        if not fks[3]:
            query += fks[0] + "." + fks[2] + " from " + table_name + " join " + \
                     fks[0] + " on " + table_name + "." + fks[1] + "=" + fks[0] + ".id" \
                     + " where " + table_name + "." + "deleted=0"

            columns.append(fks[2])
        else:
            query += fks[0] + "." + fks[2] + ", " + fks[0] + "." + fks[3] + " from " + table_name + " join " + \
                     fks[0] + " on " + table_name + "." + fks[1] + "=" + fks[0] + ".id" \
                     + " where " + table_name + "." + "deleted=0"
            columns.append(fks[2])
            columns.append(fks[3])
        if order_by_col:
            if order_by_col == fks[2] or order_by_col == fks[3]:
                query += ' order by ' + fks[0] + '.' + order_by_col + ' ' + sort_type + ';'
            else:
                query += ' order by ' + table_name + '.' + order_by_col + ' ' + sort_type + ';'
        else:
            query += ';'
        cursor.execute(query, ())
        result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result, columns


def get_foreign_keys(table_name):
    conn = sqlite3.connect('dictionary.db')
    cursor = conn.cursor()
    query = "select parent_table, child_key_name, parent_key_name, additional_info from fks_table " \
            "where child_table = ?;"
    cursor.execute(query, (table_name,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result


def choose_dict(combo, sorted_res=0, columns=0):
    chosen_dict = combo.get().lower()
    resWindow2 = Tk()
    resWindow2.title(chosen_dict.upper())
    if sorted_res:
        res = sorted_res
    else:
        res, columns = get_from_table(chosen_dict)
    tables_info, table_names = get_tables()
    table_info = tables_info[table_names.index(chosen_dict)]
    unchangeable_col = get_foreign_keys(chosen_dict)
    date_index = -1
    if 'date' in table_info:
        date_index = table_info.index('date') - 1
        date_column = table_info[date_index]
        if date_column in columns:
            date_index = columns.index(date_column)
    if unchangeable_col:
        unchangeable_col1 = unchangeable_col[0][2]
        unchangeable_col2 = unchangeable_col[0][3]
        index_unchangeable_col1 = columns.index(unchangeable_col1)
        if unchangeable_col2 is not None:
            index_unchangeable_col2 = columns.index(unchangeable_col2)
            additional_info = True
        else:
            index_unchangeable_col2 = - 1
            additional_info = False
        foreign_values = get_foreign_values(unchangeable_col[0], additional_info)

    else:
        index_unchangeable_col1, index_unchangeable_col2 = -1, -1
    if res:

        for i in range(len(res) + 1):
            entries = []
            curr_foreign_id = 0
            for j in range(len(res[0])):
                if not i:
                    col_name = columns[j].replace('_', ' ').upper()
                    lf = LabelFrame(resWindow2, borderwidth=0)
                    lf.grid(column=j, row=0)
                    result = Label(lf, text=col_name, width=25, anchor="center", relief=GROOVE)
                    result.grid(column=0, row=0)
                    sort1 = Button(lf, text='↑', width=1, height=1, anchor="w", relief=GROOVE, command=partial(
                        sorting, columns[j], 'asc', chosen_dict, combo, resWindow2))
                    sort1.grid(column=1, row=0)
                    sort2 = Button(lf, text='↓', width=1, height=1, anchor="w", relief=GROOVE, command=partial(
                        sorting, columns[j], 'desc', chosen_dict, combo, resWindow2))
                    sort2.grid(column=2, row=0)

                else:
                    if j != index_unchangeable_col1 and j != index_unchangeable_col2 and j != date_index:
                        e = Entry(resWindow2, relief=GROOVE)
                        e.grid(row=i, column=j, sticky=NSEW)
                        if 'decimal' in table_info[table_info.index(columns[j]) + 1]:
                            decimal_col = table_info[table_info.index(columns[j]) + 1].split('(')[1]
                            int_len, float_len = len(str(int(res[i - 1][j] // 1))), int(
                                decimal_col.split(', ')[1][0:-1])
                            getcontext().prec = float_len + int_len
                            decimal_res = Decimal(str(res[i - 1][j])) + Decimal('0.0')
                            e.insert(END, str(decimal_res.normalize()))
                            entries.append(e)
                            getcontext().prec = 27
                        else:
                            e.insert(END, res[i - 1][j])
                            entries.append(e)
                    if j == index_unchangeable_col1 or j == index_unchangeable_col2:

                        for_result = Label(resWindow2, text=res[i - 1][j], width=30, anchor="w", relief=GROOVE)
                        for_result.grid(column=j, row=i)
                        if index_unchangeable_col2 is None:
                            id_tuple = (res[i - 1][j],)
                            for for_value in foreign_values:
                                if id_tuple[0] == for_value[0]:
                                    curr_foreign_id = for_value[2]
                                    break

                        else:
                            id_tuple = (res[i - 1][index_unchangeable_col1], res[i - 1][index_unchangeable_col2])
                            for for_value in foreign_values:
                                if id_tuple[0] == for_value[0] and id_tuple[1] == for_value[1]:
                                    curr_foreign_id = for_value[2]

                    if j == date_index:
                        data = res[i - 1][j]
                        if '-' in data:
                            data = data.split('-')
                            year, month, day = int(data[0]), int(data[1]), int(data[2])
                        elif '/' in data:
                            data = data.split('/')
                            year, month, day = int(data[0]), int(data[1]), int(data[2])
                        elif '.' in data:
                            data = data.split('.')
                            year, month, day = int(data[2]), int(data[1]), int(data[0])
                        data = date(year, month, day)

                        calendar = DateEntry(resWindow2, width=20, background='darkblue',
                                             foreground='white', borderwidth=2, year=2022, locale='ru_RU',
                                             font="Arial 12")

                        calendar.set_date(data)
                        calendar.grid(column=j, row=i)
                        entries.append(calendar)
                    if j == len(res[0]) - 1:
                        edit_btn = Button(resWindow2, text='изменить', command=partial(new_update, res[i - 1],
                                                                                       columns, chosen_dict, resWindow2,
                                                                                       combo, table_info,
                                                                                       curr_foreign_id))
                        edit_btn.grid(column=j + 1, row=i)
                        delete_btn = Button(resWindow2, text='удалить', command=partial(delete, res[i - 1], columns,
                                                                                        chosen_dict, resWindow2, combo))

                        delete_btn.grid(column=j + 2, row=i)
        insert_btn = Button(resWindow2, text='Добавить запись', anchor='center', command=partial(insert, chosen_dict,
                                                                                                 columns, combo,
                                                                                                 resWindow2,
                                                                                                 table_info))
        insert_btn.grid(column=len(res[0]) // 2, row=i + 1)

    elif chosen_dict in get_tables()[1]:
        result = Label(resWindow2, text='В данном справочнике записей не найдено', width=50, anchor="center")
        result.grid()
        insert_btn = Button(resWindow2, text='Добавить запись', anchor='center', command=partial(insert, chosen_dict,
                                                                                                 columns, combo,
                                                                                                 resWindow2,
                                                                                                 table_info))
        insert_btn.grid()
    else:
        result = Label(resWindow2, text='Справочник с таким именем не найден', width=50, anchor="center")
        result.grid()
    resWindow2.mainloop()


def get_row_id(row, columns, table):
    conn = sqlite3.connect('dictionary.db')
    cursor = conn.cursor()
    fks = get_foreign_keys(table)
    if fks:
        joined_table, joined_col, joined_col_name, additional_info = fks[0]
    else:
        joined_col = 0
    if not joined_col:
        query = "select " + table + ".id  from " + table + " where "
        for i in range(len(columns) - 1):
            query += columns[i] + "=? and "
        query += columns[-1] + "=? and deleted=0;"
    else:
        query = "select " + table + ".id  from " + table + " join " + joined_table + " on " + joined_table + ".id" + \
                "=" + table + "." + joined_col \
                + " where "
        for i in range(len(columns) - 1):
            query += columns[i] + "=? and "
        query += columns[-1] + "=? and " + table + ".deleted=0;"
    cursor.execute(query, row)
    id = cursor.fetchone()
    cursor.close()
    conn.close()
    return id[0]


def edit(row, entries, columns, table, window, combo, table_info):
    edits = []
    id = get_row_id(row, columns, table)
    for i in range(len(entries)):
        if entries[i].get() != str(row[i]):
            if isinstance(entries[i], DateEntry):
                data = entries[i].get()
                if '-' in data:
                    try:
                        data = data.split('-')
                        year, month, day = int(data[0]), int(data[1]), int(data[2])
                    except:
                        ValueError, TypeError

                elif '/' in data:
                    try:
                        data = data.split('/')
                        year, month, day = int(data[0]), int(data[1]), int(data[2])
                    except:
                        ValueError, TypeError
                elif '.' in data:
                    try:
                        data = data.split('.')
                        year, month, day = int(data[2]), int(data[1]), int(data[0])
                    except:
                        ValueError, TypeError

                try:
                    data = date(year, month, day)
                    edits.append((columns[i], data))
                except:
                    ValueError, TypeError
            else:
                column = columns[i]
                val_type = table_info[table_info.index(column) + 1]
                if val_type == 'integer' or val_type == 'INT' or val_type == 'int':
                    try:
                        value = int(entries[i].get())
                        edits.append((column, value))
                    except:
                        ValueError, TypeError
                elif 'decimal' in val_type:
                    try:
                        value = Decimal(entries[i].get())
                        edits.append((column, str(value)))
                    except:
                        ValueError, TypeError
                elif 'varchar' in val_type and entries[i].get() != '':
                    edits.append((column, entries[i].get()))
    if edits:
        conn = sqlite3.connect('dictionary.db')
        cursor = conn.cursor()

        for e in edits:
            try:
                query = "update " + table + " set "
                query += e[0] + "=? where id=?;"
                cursor.execute(query, (e[1], id))
                conn.commit()
            except:
                messagebox.showerror('Ошибка', 'Данные введены некорректно!')
        cursor.close()
        conn.close()
    window.destroy()
    combo.set(table.upper())
    choose_dict(combo)


def new_update(curr_row, columns, table, window, main_combo, table_info, foreign_id=0):
    entries = []
    date_flag, date_index, temp_index = False, -1, -1
    for i in range(1, len(table_info)):
        if i % 2 and table_info[i] in columns:
            entries.append((table_info[i], table_info[i + 1]))
            temp_index += 1
            if table_info[i + 1] == 'date':
                date_flag, date_index = True, temp_index
    foreign_col = get_foreign_keys(table)
    updateWindow = Tk()
    new_row = []
    updateWindow.title('Изменение записи')
    for i in range(len(entries)):
        lbl = Label(updateWindow, text=entries[i][0].replace('_', ' ').upper() + ':', relief=GROOVE, width=30)
        lbl.grid(column=0, row=i)
        if i == date_index:
            data = curr_row[i]
            if '-' in data:
                data = data.split('-')
                year, month, day = int(data[0]), int(data[1]), int(data[2])

                data = date(year, month, day)

            entry = DateEntry(updateWindow, width=18, background='darkblue',
                              foreground='white', borderwidth=2, year=2022, locale='ru_RU', font="Arial 12")
            entry.set_date(data)
        else:
            entry = Entry(updateWindow, takefocus=True, width=30)
            entry.insert(END, curr_row[i])
        entry.grid(column=1, row=i)
        new_row.append(entry)
    submit = Button(updateWindow, text='Подтвердить', command=partial(edit_row, new_row, updateWindow, curr_row,
                                                                      columns, table, date_index, main_combo, window))

    if foreign_col:
        additional_info_flag = False
        foreign_id_name = foreign_col[0][1]
        if foreign_col[0][3] is not None:
            additional_info_flag = True
        foreign_values = get_foreign_values(foreign_col[0], additional_info_flag)

        foreign_values_arr = []
        for j in range(len(foreign_values)):
            if additional_info_flag:
                foreign_values_arr.append(foreign_values[j][0] + ', ' + foreign_values[j][1])
            else:
                foreign_values_arr.append(foreign_values[j][0])
        lbl = Label(updateWindow, text=foreign_col[0][2].replace('_', ' ').upper() + ':', relief=GROOVE, width=30)
        lbl.grid(column=0, row=i + 1)
        combo = Combobox(updateWindow, width=27)
        combo['values'] = foreign_values_arr
        combo.grid(column=1, row=i + 1)
        combo.set(foreign_values_arr[foreign_id - 1])
        new_row.append(combo)
        submit = Button(updateWindow, text='Подтвердить', command=partial(edit_row, new_row, updateWindow, curr_row,
                                                                          columns, table, date_index, main_combo,
                                                                          window,
                                                                          foreign_values=foreign_values, combo=combo,
                                                                          flag=additional_info_flag,
                                                                          foreign_id_name=foreign_id_name,
                                                                          curr_foreign_id=foreign_id))

    submit.grid(column=0, row=i + 2)


def edit_row(new_row, updateWindow, curr_row, columns, table, date_index, main_combo, window, foreign_values=0, combo=0,
             flag=0, foreign_id_name=0, curr_foreign_id=0):
    id = get_row_id(curr_row, columns, table)
    changed = []
    if combo:
        for i in range(len(new_row) - 1):
            if i == date_index:
                new_date = new_row[i].get().split('.')
                year, month, day = new_date[2], new_date[1], new_date[0]
                new_date = year + '-' + month + '-' + day

                if new_date != curr_row[i]:
                    try:
                        new_date = date(int(year), int(month), int(day))
                    except:
                        new_date = None
                    changed.append((columns[i], new_date))
            elif new_row[i].get() != str(curr_row[i]):
                changed.append((columns[i], new_row[i].get()))
        foreign_row = new_row[-1].get()
        foreign_row = set(foreign_row.split(', ')) if flag else {foreign_row}
        is_foreign = False
        for foreign_val in foreign_values:
            if foreign_row.issubset(foreign_val):
                is_foreign = True
                break
        foreign_id = foreign_val[-1] if is_foreign else -1
        if foreign_id != curr_foreign_id and foreign_id > 0:
            changed.append((foreign_id_name, foreign_id))
    else:
        for i in range(len(new_row)):
            if i == date_index:
                new_date = new_row[i].get().split('.')
                year, month, day = new_date[2], new_date[1], new_date[0]
                new_date = year + '-' + month + '-' + day
                if new_date != curr_row[i]:
                    changed.append((columns[i], new_date))
            elif new_row[i].get() != str(curr_row[i]):
                changed.append((columns[i], new_row[i].get()))
    if changed:
        conn = sqlite3.connect('dictionary.db')
        cursor = conn.cursor()

        for e in changed:
            try:
                query = "update " + table + " set "
                query += e[0] + "=? where id=?;"
                cursor.execute(query, (e[1], id))
                conn.commit()
            except:
                messagebox.showerror('Ошибка', 'Данные введены некорректно!')
        cursor.close()
        conn.close()
    window.destroy()
    updateWindow.destroy()
    main_combo.set(table.upper())
    choose_dict(main_combo)


def delete(row, columns, table, window, combo):
    id = get_row_id(row, columns, table)
    conn = sqlite3.connect('dictionary.db')
    cursor = conn.cursor()
    query = "update " + table + " set deleted=1 where id=?;"
    answer = messagebox.askyesno("Удаление", "Вы действительно хотите удалить запись?")
    if answer:
        cursor.execute(query, (id,))
        conn.commit()
        window.destroy()
        combo.set(table.upper())
        choose_dict(combo)
    cursor.close()
    conn.close()


def get_foreign_values(info, additional_info_flag):
    conn = sqlite3.connect('dictionary.db')
    cursor = conn.cursor()
    if additional_info_flag:
        query = "select " + info[2] + ", " + info[3] + ", id from " + info[0] + " where deleted=0;"
    else:
        query = "select " + info[2] + ", id from " + info[0] + " where deleted=0;"
    cursor.execute(query, ())
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result


def insert(table, columns, main_combo, resWindow, table_info):
    entries, row = [], []
    date_flag, date_index, temp_index = False, -1, -1
    for i in range(1, len(table_info)):
        if i % 2 and table_info[i] in columns:
            entries.append((table_info[i], table_info[i + 1]))
            temp_index += 1
            if table_info[i + 1] == 'date':
                date_flag, date_index = True, temp_index
    foreign_col = get_foreign_keys(table)
    insertWindow = Tk()
    insertWindow.title('Добавление записи')
    for i in range(len(entries)):
        lbl = Label(insertWindow, text=entries[i][0].replace('_', ' ').upper() + ':', relief=GROOVE, width=30)
        lbl.grid(column=0, row=i)
        if i == date_index:
            entry = DateEntry(insertWindow, width=18, background='darkblue',
                              foreground='white', borderwidth=2, year=2022, locale='ru_RU', font="Arial 12")
        else:
            entry = Entry(insertWindow, takefocus=True, width=30)
        entry.grid(column=1, row=i)
        row.append(entry)
    submit = Button(insertWindow, text='Подтвердить', command=partial(insert_row, insertWindow, row, columns, table,
                                                                      main_combo, resWindow))
    if foreign_col:
        additional_info_flag = False
        foreign_id_name = foreign_col[0][1]
        if foreign_col[0][3] is not None:
            additional_info_flag = True
        foreign_values = get_foreign_values(foreign_col[0], additional_info_flag)
        foreign_values_arr = []
        for j in range(len(foreign_values)):
            if additional_info_flag:
                foreign_values_arr.append(foreign_values[j][0] + ', ' + foreign_values[j][1])
            else:
                foreign_values_arr.append(foreign_values[j][0])
        lbl = Label(insertWindow, text=foreign_col[0][2].replace('_', ' ').upper() + ':', relief=GROOVE, width=30)
        lbl.grid(column=0, row=i + 1)
        combo = Combobox(insertWindow, width=27)
        combo['values'] = foreign_values_arr
        combo.grid(column=1, row=i + 1)
        submit = Button(insertWindow, text='Подтвердить', command=partial(insert_row, insertWindow, row, columns, table,
                                                                          main_combo, resWindow,
                                                                          foreign_values=foreign_values, combo=combo,
                                                                          flag=additional_info_flag,
                                                                          foreign_id_name=foreign_id_name))
    submit.grid(column=0, row=i + 2)
    insertWindow.mainloop()


def insert_row(window, entries, columns, table, main_combo, resWindow, foreign_values=0, combo=0, flag=False,
               foreign_id_name=''):
    row = []
    for e in entries:
        row.append(e.get())
    tables, table_names = get_tables()
    table_info = tables[table_names.index(table)]
    values, val_types = [], []
    for i in range(len(row)):
        val = ''
        val_type = table_info[table_info.index(columns[i]) + 1]
        if 'varchar' in val_type:
            val_types.append('varchar')
            val = row[i]
        elif 'decimal' in val_type:
            val_types.append('decimal')
            try:
                val = Decimal(row[i])
            except:
                ValueError, TypeError
        elif 'date' in val_type:
            val_types.append('date')
            data = row[i].split('.')
            try:
                val = date(int(data[2]), int(data[1]), int(data[0]))
            except:
                ValueError, TypeError
        elif 'integer' or 'INT' in val_type:
            val_types.append('int')
            try:
                val = int(row[i])
            except:
                ValueError, TypeError
        values.append(val)
    if combo:
        foreign_val = combo.get()
        id = 0
        if flag:
            foreign_val = foreign_val.split(', ')
            for for_col in foreign_values:
                if foreign_val[0] in for_col and foreign_val[1] in for_col:
                    id = for_col[2]
        else:
            for for_col in foreign_values:
                if foreign_val in for_col:
                    id = for_col[1]
        values.append(id)
        val_types.append('int')
    is_valid = isValid(values, val_types)

    if not is_valid:
        showerror(title="Ошибка", message="Данные введены некорректно!")

    else:
        result, columns = get_from_table(table)
        is_in_table = False
        if result:
            for i in range(len(result)):
                for j in range(len(values)):
                    if str(result[i][j]) != str(values[j]):
                        break
                    else:
                        if j == len(values) - 1:
                            is_in_table = True

        if is_in_table:
            showerror(title="Ошибка!", message="Данная запись есть в справочнике")
        else:
            query_tuple = ()
            conn = sqlite3.connect('dictionary.db')
            cursor = conn.cursor()
            try:
                query = "insert into " + table + " ("
                if not combo:
                    for i in range(len(columns) - 1):
                        query += columns[i] + ', '
                    query += columns[-1] + ') values('
                    for i in range(len(values) - 1):
                        query += '?, '
                        query_tuple += (str(values[i]),)
                    query_tuple += (str(values[-1]),)
                    query += '?);'
                else:
                    if flag:
                        for i in range(len(columns) - 2):
                            query += columns[i] + ', '
                    else:
                        for i in range(len(columns) - 1):
                            query += columns[i] + ', '
                    query += foreign_id_name + ') values('
                    for i in range(len(values) - 1):
                        query += '?, '
                        query_tuple += (str(values[i]),)
                    query += '?);'
                    query_tuple += (str(values[-1]),)
                cursor.execute(query, query_tuple)
                conn.commit()
            except:
                messagebox.showerror('Ошибка', 'Данные введены некорректно!')
            cursor.close()
            conn.close()
            window.destroy()
            resWindow.destroy()
            main_combo.set(table.upper())
            choose_dict(main_combo)


def isValid(values, val_types):
    if '' in values:
        return False
    for i in range(len(values)):
        if val_types[i] == 'int' and (values[i] <= 0 or values[i] >= 2500):
            return False
        elif val_types[i] == 'date' and (values[i].year < 500 or values[i].year > date.today().year):
            return False
        elif val_types[i] == 'decimal' and (values[i] <= 0 or values[i] >= 250000):
            return False
    return True


def interface():
    tables, table_names = get_tables()
    dictionaries = [table_name.upper() for table_name in table_names]
    window = Tk()
    window.title('Справочник')
    window.geometry('300x90')
    name = Label(window, text="Ковалёв Иван Романович, 4 к. 4 гр., 2022", width=40, anchor='center')
    name.grid(column=0, row=0)
    name_lbl = Label(window, width=40, text='Выберите справочник:')
    name_lbl.grid(column=0, row=1)
    combo = Combobox(window, width=20)
    combo['values'] = dictionaries
    combo.grid(column=0, row=2)
    btn = Button(window, text='Выбор', command=partial(choose_dict, combo))
    btn.grid(column=0, row=3)
    window.mainloop()


def sorting(col_name, sort_type, table, combo, window):
    sorted_res, columns = get_from_table(table, col_name, sort_type)
    window.destroy()
    combo.set(table.upper())
    choose_dict(combo, sorted_res, columns)


interface()
