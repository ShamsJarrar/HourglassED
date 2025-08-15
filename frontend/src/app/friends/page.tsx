export default function FriendsPage() {
  return (
    <div className="min-h-screen py-8" style={{ backgroundColor: '#FFF8EB' }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold" style={{ color: '#633D00' }}>Friends</h1>
          <p className="mt-2" style={{ color: '#633D00' }}>Connect with classmates and study partners</p>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="rounded-xl shadow-md p-6" style={{ backgroundColor: '#FAF0DC' }}>
            <h3 className="text-lg font-semibold mb-4" style={{ color: '#633D00' }}>Your Friends</h3>
            <div className="text-center py-8">
              <div className="text-4xl mb-3">👥</div>
              <p style={{ color: '#633D00' }} className="opacity-70">Friends list will appear here</p>
            </div>
          </div>
          
          <div className="rounded-xl shadow-md p-6" style={{ backgroundColor: '#FAF0DC' }}>
            <h3 className="text-lg font-semibold mb-4" style={{ color: '#633D00' }}>Friend Requests</h3>
            <div className="text-center py-8">
              <div className="text-4xl mb-3">📬</div>
              <p style={{ color: '#633D00' }} className="opacity-70">Pending friend requests will appear here</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}