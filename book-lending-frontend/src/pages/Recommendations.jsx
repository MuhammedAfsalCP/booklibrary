import { useQuery } from '@tanstack/react-query';
import API from '../api/axios';

export default function Recommendations() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['recommendations'],
    queryFn: async () => {
      const res = await API.get('recommendations/');
      return res.data;
    },
  });

  if (isLoading) return <div className="p-6 text-gray-600">Loading recommended books...</div>;
  if (isError) return <div className="p-6 text-red-600">Error loading recommendations</div>;


  const recommendations = Array.isArray(data) ? data : data?.results || [];

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <h2 className="text-2xl font-semibold text-gray-800 mb-6">Recommended Books</h2>
      {recommendations.length === 0 ? (
        <p className="text-gray-600">No recommendations available at the moment.</p>
      ) : (
        <ul className="space-y-4">
          {recommendations.map((book) => (
            <li key={book.id} className="bg-white p-4 rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200">
              <span className="font-semibold text-gray-800">{book.title}</span> - Author: {book.author} - Popularity: {book.read_count}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}