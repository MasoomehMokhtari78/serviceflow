import React from 'react';
import type { OrderItemStatusEnum, OrderStatusEnum } from '../../types';
import { getItemStatusInfo, getOrderStatusInfo } from '../../utils/formatters';

interface StatusBadgeProps {
  status: OrderStatusEnum | OrderItemStatusEnum;
  type?: 'order' | 'item';
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, type = 'order', className = '' }) => {
  const info = type === 'order' 
    ? getOrderStatusInfo(status as OrderStatusEnum) 
    : getItemStatusInfo(status as OrderItemStatusEnum);

  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium border ${info.bg} ${info.text} ${info.border} ${className}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current ml-1.5 animate-pulse" />
      {info.label}
    </span>
  );
};
