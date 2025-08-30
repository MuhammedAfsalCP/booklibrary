import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import API from '../api/axios';

export default function Books() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);

  const [filters, setFilters] = useState({ genre: '', author: '', available: '' });
  const [appliedFilters, setAppliedFilters] = useState({ genre: '', author: '', available: '' });

  const { data, isLoading, isError } = useQuery({
    queryKey: ['books', page, appliedFilters],
    queryFn: async () => {
      const params = new URLSearchParams({ ...appliedFilters, page }).toString();
      const res = await API.get(`books/?${params}`);
      return res.data;
    },
    keepPreviousData: true,
  });

  const { data: borrowedData } = useQuery({
    queryKey: ['my-borrows'],
    queryFn: async () => {
      const res = await API.get('my-borrows/');
      return res.data;
    },
  });

  const borrowMutation = useMutation({
    mutationFn: (bookId) => API.post('borrow/', { book_id: bookId }),
    onSuccess: () => {
      queryClient.invalidateQueries(['books', page]);
      queryClient.invalidateQueries(['my-borrows']);
    },
  });

  const returnMutation = useMutation({
    mutationFn: (bookId) => API.post('return/', { book_id: bookId }),
    onSuccess: () => {
      queryClient.invalidateQueries(['books', page]);
偶

System: queryClient.invalidateQueries(['my-borrows']);
    },
  });

  if (isLoading) return <div className="p-6 text-gray-600">Loading books...</div>;
  if (isError) return <div className="p-6 text-red-600">Error loading books</div>;

  const books = Array.isArray(data.results) ? data.results : [];
  const borrowedBooks = Array.isArray(borrowedData) ? borrowedData : [];
  const borrowedBookIds = borrowedBooks.map((b) => b.book.id);

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <h2 className="text-2xl font-semibold text-gray-800 mb-6">All Books</h2>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 mb-8 bg-white p-4 rounded-lg shadow-sm">
        <input
          type="text"
          placeholder="Author"
          value={filters.author}
          onChange={(e) => setFilters({ ...filters, author: e.target.value })}
          className="border border-gray-300 p-2 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-400 w-64"
        />
        <input
          type="text"
          placeholder="Genre"
          value={filters.genre}
          onChange={(e) => setFilters({ ...filters, genre: e.target.value })}
          className="border border-gray-300 p-2 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-400 w-64"
        />
        <select
          value={filters.available}
          onChange={(e) => setFilters({ ...filters, available: e.target.value })}
          className="border border-gray-300 p-2 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-400 w-64"
        >
          <option value="">Availability</option>
          <option value="true">Available</option>
          <option value="false">Not Available</option>
        </select>
        <button
          onClick={() => {
            setAppliedFilters(filters); // Apply filters only on button click
            setPage(1); 
          }}
          className="bg-gray-700 text-white px-4 py-2 rounded-md hover:bg-gray-800 transition-colors duration-200"
        >
          Apply Filters
        </button>
      </div>


      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {books.map((book) => {
          const isBorrowed = borrowedBookIds.includes(book.id);
          return (
            <div key={book.id} className="bg-white p-5 rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200">
              <h3 className="font-semibold text-lg text-gray-800 mb-2">{book.title}</h3>
              <p className="text-gray-600 mb-1">Author: {book.author}</p>
              <p className="text-gray-600 mb-1">Genre: {book.genre}</p>
              <p className="text-gray-600 mb-4">
                Available: {book.available_copies > 0 ? 'Yes' : 'No'}
              </p>

              {!isBorrowed && book.available_copies > 0 && (
                <button
                  onClick={() => borrowMutation.mutate(book.id)}
                  className="bg-gray-700 text-white px-4 py-2 rounded-md hover:bg-gray-800 transition-colors duration-200"
                >
                  Borrow
                </button>
              )}

              {isBorrowed && (
                <button
                  onClick={() => returnMutation.mutate(book.id)}
                  className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 transition-colors duration-200"
                >
                  Return
                </button>
              )}
            </div>
          );
        })}
      </div>


      <div className="flex justify-center mt-8 space-x-4">
        <button
          onClick={() => setPage((old) => Math.max(old - 1, 1))}
          disabled={page === 1}
          className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 disabled:opacity-50 transition-colors duration-200"
        >
          Previous
        </button>
        <span className="px-4 py-2 text-gray-700">Page {page}</span>
        <button
          onClick={() => setPage((old) => old + 1)}
          disabled={!data.next}
          className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 disabled:opacity-50 transition-colors duration-200"
        >
          Next
        </button>
      </div>
    </div>
  );
}