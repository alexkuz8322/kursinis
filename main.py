import csv
from datetime import datetime
import yaml
import json


def parse_date(date_str, date_format):
    try:
        date = datetime.strptime(date_str, date_format)
        return date
    except ValueError:
        print(f"Invalid date format: {date_str}. Please use the format 'YYYY-MM-DD'.")
        return None


def get_time_ranges(date_list):
    time_ranges = []
    date_format = config.get('date_format', '%Y-%m-%d')
    print("Available time ranges:")
    for i, date in enumerate(date_list):
        print(f"{i + 1}. {date}")


    while True:        
        start_choice = input("Choose a start date (enter the corresponding number) or press the enter button for all time ranges, or 'q' to finish: ")
        if start_choice.lower() == 'q':
            break
        if start_choice == '':
            time_ranges = [(parse_date(date_list[0], date_format), parse_date(date_list[-1], date_format))]
            print("All time ranges selected.")
            break

        if start_choice.isdigit() and 1 <= int(start_choice) <= len(date_list):
            start_date = parse_date(date_list[int(start_choice) - 1], date_format)

            end_choice = input("Choose an end date (enter the corresponding number): ")
            if end_choice.isdigit() and 1 <= int(end_choice) <= len(date_list):
                end_date = parse_date(date_list[int(end_choice) - 1], date_format)

                end_date = end_date.replace(hour=23, minute=59, second=59)

                time_ranges.append((start_date, end_date))
                print(f"Selected time range: {start_date} to {end_date}")
            else:
                print("Invalid input. Please try again.")
        else:
            print("Invalid input. Please try again.")

    return time_ranges



def filter_by_time_range(input_file_path):
    with open(input_file_path, 'r') as input_file:
        reader = csv.reader(input_file)
        date_list = []
        unsorted_data = []
        for row in reader:
            if row[config['date_column_index']] != 'date':
                timestamp = int(row[config['date_column_index']]) // 1000
                date_obj = datetime.fromtimestamp(timestamp)
                formatted_date = date_obj.strftime(config['date_format'])
                if formatted_date not in date_list:
                    date_list.append(formatted_date)
                unsorted_data.append(row)

        date_list.sort()

        if not date_list:
            print("No available time ranges.")
            return

        time_ranges = get_time_ranges(date_list)

        if time_ranges:
            print("Selected time range(s):")
            for i, time_range in enumerate(time_ranges):
                print(f"{i + 1}. {time_range[0]} to {time_range[1]}")

            filter_by_users(input_file_path, unsorted_data, time_ranges)
        else:
            print("No valid time range selection. Please try again.")
            filter_by_time_range(input_file_path)


def filter_by_users(input_file_path, unsorted_data, time_ranges):
    with open(input_file_path, 'r') as input_file:
        reader = csv.reader(input_file)
        next(reader)
        user_list = []
        for row in reader:
            if row[config['address_column_index']] not in user_list:
                user_list.append(row[config['address_column_index']])
        user_list.sort()

        if not user_list:
            print("No available users.")
            return

        print("Available users:")
        for i, user in enumerate(user_list):
            print(f"{i + 1}. {user}")
        
        user_choice = input("Choose user(s) by entering the corresponding number(s), separated by commas (press ENTER button for all users) ")
        if user_choice:
            user_indices = [int(index) - 1 for index in user_choice.split(',') if 1 <= int(index) <= len(user_list)]
            selected_users = [user_list[index] for index in user_indices]

            if not selected_users:
                print("No valid user selection. Please try again.")
                filter_by_users(input_file_path, unsorted_data, time_ranges)

            filter_data(input_file_path, unsorted_data, selected_users, time_ranges)
        else:
            filter_data(input_file_path, unsorted_data, [], time_ranges)

def filter_data(input_file_path, unsorted_data, selected_users, time_ranges):
    filtered_data = []
    user_interaction_counts = {}
    user_time_range_interactions = {}

    for row in unsorted_data:
        timestamp = int(row[config['date_column_index']]) // 1000
        date_obj = datetime.fromtimestamp(timestamp)

        if any(start_date <= date_obj <= end_date for start_date, end_date in time_ranges) and \
                (not selected_users or row[config['address_column_index']] in selected_users):
            filtered_data.append(row)

 
            user = row[config['address_column_index']]
            user_interaction_counts[user] = user_interaction_counts.get(user, 0) + 1

            for start_date, end_date in time_ranges:
                if start_date <= date_obj <= end_date:
                    time_range_key = f"{start_date.strftime(config['date_format'])}-{end_date.strftime(config['date_format'])}"
                    if user not in user_time_range_interactions:
                        user_time_range_interactions[user] = []
                    user_time_range_interactions[user].append(date_obj.strftime('%Y-%m-%d %H:%M:%S'))
                    break

    filtered_data.sort(key=lambda x: int(x[config['date_column_index']]))

    with open(config['output_file_path'], 'w', newline='') as output_file, \
            open(config['unsorted_file_path'], 'w', newline='') as unsorted_file, \
            open(config['statistics_file_path'], 'w') as stats_file:
        
        writer = csv.writer(output_file)
        unsorted_writer = csv.writer(unsorted_file)

        header = ['type', 'id', 'address', 'date', 'body']
        writer.writerow(header)
        unsorted_writer.writerow(header)

        if not filtered_data:
            writer.writerow(["No data found for the selected user(s) in the chosen time range(s)"])

        for row in filtered_data:
            timestamp = int(row[config['date_column_index']]) // 1000
            date_obj = datetime.fromtimestamp(timestamp)
            formatted_date = date_obj.strftime('%Y-%m-%d %H:%M:%S')
            writer.writerow(row[:3] + [formatted_date] + row[4:])

        for row in unsorted_data:
            timestamp = int(row[config['date_column_index']]) // 1000
            date_obj = datetime.fromtimestamp(timestamp)
            formatted_date = date_obj.strftime('%Y-%m-%d %H:%M:%S')
            unsorted_writer.writerow(row[:3] + [formatted_date] + row[4:])

       
        statistics = []
        for user, count in user_interaction_counts.items():
            dates_str = user_time_range_interactions.get(user, [])
            user_stats = {
                "User": user,
                "Interactions": count,
                "Dates": dates_str
            }
            statistics.append(user_stats)

        json.dump(statistics, stats_file, indent=4)

    print("Filtered data has been written to output.csv.")
    print("Unsorted information has been written to unsorted_info.csv.")
    print("Statistics have been written to statistics.json.")





def main():
    filter_by_time_range(config['input_file_path'])


if __name__ == '__main__':
    # Load the configuration file
    with open('config.yaml', 'r') as config_file:
        config = yaml.safe_load(config_file)

    main()



