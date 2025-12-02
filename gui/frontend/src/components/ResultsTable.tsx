import { useState, useMemo } from 'react';
import { ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';
import SearchBar from './SearchBar';

interface Column {
  key: string;
  label: string;
  sortable?: boolean;
  render?: (value: any, row: any) => React.ReactNode;
}

interface ResultsTableProps {
  columns: Column[];
  data: any[];
  searchPlaceholder?: string;
  emptyMessage?: string;
}

/**
 * Results table with search, filter, and sort capabilities
 * 
 * @param columns - Column definitions
 * @param data - Table data
 * @param searchPlaceholder - Placeholder for search box
 * @param emptyMessage - Message to show when no data
 */
export default function ResultsTable({ 
  columns, 
  data, 
  searchPlaceholder = 'Search results...',
  emptyMessage = 'No results found'
}: ResultsTableProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  // Memoize string values for search to avoid repeated conversions
  const searchableData = useMemo(() => {
    return data.map(row => {
      const searchText = columns.map(col => {
        const value = row[col.key];
        return value !== null && value !== undefined ? String(value).toLowerCase() : '';
      }).join(' ');
      return { row, searchText };
    });
  }, [data, columns]);

  // Filter data based on search query
  const filteredData = useMemo(() => {
    if (!searchQuery) return data;
    
    const query = searchQuery.toLowerCase();
    return searchableData
      .filter(item => item.searchText.includes(query))
      .map(item => item.row);
  }, [searchableData, data, searchQuery]);

  // Sort filtered data
  const sortedData = useMemo(() => {
    if (!sortColumn) return filteredData;
    
    return [...filteredData].sort((a, b) => {
      const aVal = a[sortColumn];
      const bVal = b[sortColumn];
      
      if (aVal === bVal) return 0;
      
      let comparison = 0;
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        comparison = aVal - bVal;
      } else {
        comparison = String(aVal).localeCompare(String(bVal));
      }
      
      return sortDirection === 'asc' ? comparison : -comparison;
    });
  }, [filteredData, sortColumn, sortDirection]);

  const handleSort = (columnKey: string) => {
    if (sortColumn === columnKey) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(columnKey);
      setSortDirection('asc');
    }
  };

  const getSortIcon = (columnKey: string) => {
    if (sortColumn !== columnKey) {
      return <ArrowUpDown className="h-4 w-4 ml-1 inline text-gray-400 dark:text-gray-500" />;
    }
    return sortDirection === 'asc' 
      ? <ArrowUp className="h-4 w-4 ml-1 inline text-blue-600 dark:text-blue-400" />
      : <ArrowDown className="h-4 w-4 ml-1 inline text-blue-600 dark:text-blue-400" />;
  };

  return (
    <div>
      {/* Search Bar */}
      <div className="mb-4">
        <SearchBar 
          placeholder={searchPlaceholder}
          onSearch={setSearchQuery}
        />
        {searchQuery && (
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
            Found {sortedData.length} result{sortedData.length !== 1 ? 's' : ''}
          </p>
        )}
      </div>

      {/* Table */}
      {sortedData.length === 0 ? (
        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
          {searchQuery ? `No results match "${searchQuery}"` : emptyMessage}
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                {columns.map(col => (
                  <th
                    key={col.key}
                    className={`px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider ${
                      col.sortable !== false ? 'cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600' : ''
                    }`}
                    onClick={() => col.sortable !== false && handleSort(col.key)}
                  >
                    {col.label}
                    {col.sortable !== false && getSortIcon(col.key)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {sortedData.map((row, idx) => (
                <tr key={idx} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                  {columns.map(col => (
                    <td key={col.key} className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100">
                      {col.render ? col.render(row[col.key], row) : row[col.key]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
