import React, { useState, useEffect } from 'react';
import { useAuth } from './context/AuthContext';
import { LoginPage } from './components/auth/LoginPage';
import { Navbar } from './components/common/Navbar';
import { ActiveOrders } from './components/waiter/ActiveOrders';
import { CreateOrderModal } from './components/waiter/CreateOrderModal';
import { OrderDetailsDrawer } from './components/waiter/OrderDetailsDrawer';
import { KitchenQueue } from './components/kitchen/KitchenQueue';
import { ManagerDashboard } from './components/manager/ManagerDashboard';
import { AIAnalystSection } from './components/manager/AIAnalystSection';
import { api } from './services/api';
import type { BranchOut, OrderOut } from './types';
import { Coffee, Store } from 'lucide-react';

export const AppContent: React.FC = () => {
  const { user, isLoading } = useAuth();
  const [currentTab, setCurrentTab] = useState<string>('orders');
  const [branches, setBranches] = useState<BranchOut[]>([]);
  const [selectedBranchId, setSelectedBranchId] = useState<string>('');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState<boolean>(false);
  const [selectedOrder, setSelectedOrder] = useState<OrderOut | null>(null);

  // Set initial tab based on role
  useEffect(() => {
    if (user) {
      const userRole = user.role?.toLowerCase();
      if (userRole === 'kitchen') {
        setCurrentTab('kitchen');
      } else if (userRole === 'waiter' || userRole === 'manager') {
        setCurrentTab('orders');
      }
    }
  }, [user]);

  // Load branches
  useEffect(() => {
    if (!user) return;

    async function loadBranches() {
      try {
        const data = await api.restaurants.getBranches();
        setBranches(data);

        // If user already has an assigned branch, use it; otherwise use the first branch
        if (user?.branch_id) {
          setSelectedBranchId(user.branch_id);
        } else if (data.length > 0) {
          setSelectedBranchId(data[0].id);
        }
      } catch (err) {
        console.error('Failed to load branches:', err);
      }
    }

    loadBranches();
  }, [user]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-stone-950 flex flex-col items-center justify-center space-y-4">
        <div className="w-12 h-12 rounded-2xl bg-amber-600/20 border border-amber-600/40 flex items-center justify-center text-amber-500 animate-pulse">
          <Coffee className="w-7 h-7" />
        </div>
        <div className="text-stone-300 text-sm font-semibold">
          در حال راه‌اندازی و احراز هویت سرویس‌فلو...
        </div>
      </div>
    );
  }

  if (!user) {
    return <LoginPage />;
  }

  const currentBranch = branches.find((b) => b.id === selectedBranchId);

  return (
    <div className="min-h-screen bg-stone-950 text-stone-100 flex flex-col">
      {/* Top Navigation */}
      <Navbar
        currentTab={currentTab}
        onTabChange={(tab) => setCurrentTab(tab)}
        onOpenCreateOrder={() => setIsCreateModalOpen(true)}
        branchName={currentBranch?.name}
      />

      {/* Manager Branch Switcher (if user is manager) */}
      {user.role?.toLowerCase() === 'manager' && branches.length > 1 && (
        <div className="bg-stone-900/60 border-b border-stone-800/80 px-4 py-2">
          <div className="max-w-7xl mx-auto flex items-center justify-between text-xs">
            <span className="text-stone-400 flex items-center">
              <Store className="w-3.5 h-3.5 ml-1.5 text-amber-500" />
              مدیریت شعبه فعال:
            </span>
            <div className="flex space-x-1 space-x-reverse">
              {branches.map((b) => (
                <button
                  key={b.id}
                  onClick={() => setSelectedBranchId(b.id)}
                  className={`px-3 py-1 rounded-lg transition-colors font-medium ${
                    selectedBranchId === b.id
                      ? 'bg-amber-600 text-white shadow'
                      : 'text-stone-400 hover:text-stone-200 hover:bg-stone-800'
                  }`}
                >
                  {b.name}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {currentTab === 'orders' && (
          <ActiveOrders
            branchId={selectedBranchId}
            onOpenCreateOrder={() => setIsCreateModalOpen(true)}
            onSelectOrder={(order) => setSelectedOrder(order)}
          />
        )}

        {currentTab === 'kitchen' && (
          <KitchenQueue branchId={selectedBranchId} />
        )}

        {currentTab === 'metrics' && (
          <ManagerDashboard branchId={selectedBranchId} />
        )}

        {currentTab === 'ai' && (
          <AIAnalystSection branchId={selectedBranchId} />
        )}
      </main>

      {/* Create Order Modal */}
      <CreateOrderModal
        branchId={selectedBranchId}
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onOrderCreated={() => {
          // If in orders view, it refreshes automatically
        }}
      />

      {/* Order Details Drawer */}
      <OrderDetailsDrawer
        order={selectedOrder}
        isOpen={!!selectedOrder}
        onClose={() => setSelectedOrder(null)}
        onOrderUpdated={() => {
          setSelectedOrder(null);
        }}
      />
    </div>
  );
};

export const App: React.FC = () => {
  return <AppContent />;
};

export default App;
