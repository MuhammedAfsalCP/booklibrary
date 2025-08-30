import { useQuery } from '@tanstack/react-query';
import API from '../api/axios';

export default function BorrowedBooks() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['my-borrows'],
    queryFn: async () => {
      const res = await API.get('my-borrows/');
      return res.data;
    },
  });

  if (isLoading) return <div className="p-6 text-gray-600">Loading borrowed books...</div>;
  if (isError) return <div className="p-6 text-red-600">Error loading borrowed books</div>;


  const borrows = Array.isArray(data) ? data : data?.results || [];

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <h2 className="text-2xl font-semibold text-gray-800 mb-6">My Borrowed Books</h2>
      {borrows.length === 0 ? (
        <p className="text-gray-600">You have no borrowed books currently.</p>
      ) : (
        <ul className="space-y-4">
          {borrows.map((b) => (
            <li key={b.id} className="bg-white p-4 rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200">
              <span className="font-semibold text-gray-800">{b.book.title}</span> - Borrowed on:{' '}
              {new Date(b.borrowed_at).toLocaleDateString()}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}