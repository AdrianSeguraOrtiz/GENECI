import argparse
import pandas as pd
import numpy as np

def main(file_path, column, num_points, mode):
    # Read the CSV file while skipping the first header row and interpreting the second row as actual column names
    data = pd.read_csv(file_path, skiprows=[0])
    
    # Sort the dataframe by the specified column in descending order
    sorted_data = data.sort_values(by=column, ascending=False)
    
    if mode == "best":
        # Select the top `num_points` rows
        top_rows = sorted_data.head(num_points)
    
    elif mode == "neighbor":
        # Columns to use for distance calculation
        coord_columns = ['quality', 'degreedistribution', 'motifs']
        
        # Create a normalized version of the columns for distance calculation only
        normalized_data = sorted_data.copy()
        normalized_data[coord_columns] = (sorted_data[coord_columns] - sorted_data[coord_columns].min()) / (sorted_data[coord_columns].max() - sorted_data[coord_columns].min())
    
        # Get the best row (first row after sorting)
        best_row = normalized_data.iloc[0]
        
        # Compute the Euclidean distances to the best row using the normalized columns
        normalized_data['distance'] = np.linalg.norm(normalized_data[coord_columns] - best_row[coord_columns], axis=1)
        
        # Sort by distance to the best row (ascending) and select the best row plus `num_points - 1` neighbors
        neighbors = normalized_data.nsmallest(num_points, 'distance')
        
        # Retrieve the original data for these neighbors
        top_rows = sorted_data.loc[neighbors.index]

    else:
        raise ValueError("Invalid mode. Use 'best' or 'neighbor'.")
    
    # Calculate the maximum value for each required column across the selected rows
    max_values = top_rows[['quality', 'degreedistribution', 'motifs']].max()
    
    # Print the results in the desired format
    print(f"{max_values['quality']};{max_values['degreedistribution']};{max_values['motifs']}")

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Extract specific values from a CSV file.")
    parser.add_argument("file_path", type=str, help="Path to the input CSV file.")
    parser.add_argument("column", type=str, help="Column to sort by in the CSV file.")
    parser.add_argument("num_points", type=int, help="Number of points to contemplate.")
    parser.add_argument("mode", type=str, choices=["best", "neighbor"], help="Selection mode: 'best' or 'neighbor'.")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute the main function
    main(args.file_path, args.column, args.num_points, args.mode)