import argparse
import pandas as pd

def main(file_path, column, num_points):
    # Read the CSV file while skipping the first header row and interpreting the second row as actual column names
    data = pd.read_csv(file_path, skiprows=[0])
    
    # Sort the dataframe by the specified column in descending order
    sorted_data = data.sort_values(by=column, ascending=False)
    
    # Select the top `num_points` rows
    top_rows = sorted_data.head(num_points)
    
    # Calculate the maximum value for each required column across the top rows
    max_values = top_rows[['quality', 'degreedistribution', 'motifs']].max()
    
    # Print the results in the desired format
    print(f"{max_values['quality']};{max_values['degreedistribution']};{max_values['motifs']}")

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Extract specific values from a CSV file.")
    parser.add_argument("file_path", type=str, help="Path to the input CSV file.")
    parser.add_argument("column", type=str, help="Columns to extract from the CSV file.")
    parser.add_argument("num_points", type=int, help="Number of points to contemplate.")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute the main function
    main(args.file_path, args.column, args.num_points)
