import api from "./api";

function getErrorMessage(error, fallbackMessage) {
  const detail = error.response?.data?.detail;

  return typeof detail === "string" ? detail : error.message || fallbackMessage;
}

export async function createOrder(orderData) {
  try {
    const response = await api.post("/api/orders", orderData);
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, "Porosia nuk mund të ruhet."));
  }
}

export async function getOrders() {
  try {
    const response = await api.get("/api/orders");
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, "Porositë nuk mund të ngarkohen."));
  }
}
export async function getKitchenOrders() {
  try {
    const response = await api.get("/api/orders/kitchen");

    return response.data;
  } catch (error) {
    throw new Error(
      getErrorMessage(error, "Porositë e kuzhinës nuk mund të ngarkohen."),
    );
  }
}
export async function updateKitchenStatus(orderId, status) {
  try {
    const response = await api.patch(`/api/orders/${orderId}/kitchen-status`, {
      status,
    });

    return response.data;
  } catch (error) {
    throw new Error(
      getErrorMessage(
        error,
        "Statusi i porosisë së kuzhinës nuk mund të ndryshohet.",
      ),
    );
  }
}
export async function getOrderById(orderId) {
  try {
    const response = await api.get(`/api/orders/${orderId}`);
    return response.data;
  } catch (error) {
    throw new Error(
      getErrorMessage(error, "Porosia ekzistuese nuk mund të ngarkohet."),
    );
  }
}

export async function updateOrder(orderId, orderData) {
  try {
    const response = await api.put(`/api/orders/${orderId}`, orderData);
    return response.data;
  } catch (error) {
    throw new Error(
      getErrorMessage(error, "Porosia nuk mund të përditësohet."),
    );
  }
}
export async function updateOrderStatus(orderId, orderStatus) {
  try {
    const response = await api.patch(`/api/orders/${orderId}/status`, {
      status: orderStatus,
    });

    return response.data;
  } catch (error) {
    throw new Error(
      getErrorMessage(error, "Statusi i porosisë nuk mund të përditësohet."),
    );
  }
}

export async function payOrder(orderId, paymentMethod) {
  try {
    const response = await api.patch(`/api/orders/${orderId}/pay`, {
      payment_method: paymentMethod,
    });

    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, "Pagesa nuk mund të përfundohet."));
  }
}

export async function cancelOrder(orderId) {
  try {
    const response = await api.patch(`/api/orders/${orderId}/cancel`);
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, "Porosia nuk mund të anulohet."));
  }
}

export async function resetDemoOrders() {
  try {
    const response = await api.delete("/api/orders/reset-demo");
    return response.data;
  } catch (error) {
    throw new Error(
      getErrorMessage(error, "Porositë demo nuk mund të fshihen."),
    );
  }
}
export async function getBarOrders() {
  try {
    const response = await api.get("/api/orders/bar");
    return response.data;
  } catch (error) {
    throw new Error(
      getErrorMessage(error, "Porositë e barit nuk mund të ngarkohen."),
    );
  }
}

export async function updateBarStatus(orderId, status) {
  try {
    const response = await api.patch(`/api/orders/${orderId}/bar-status`, {
      status,
    });

    return response.data;
  } catch (error) {
    throw new Error(
      getErrorMessage(
        error,
        "Statusi i porosisë së barit nuk mund të ndryshohet.",
      ),
    );
  }
}
export async function addItemsToOrder(orderId, items) {
  try {
    const response = await api.post(`/api/orders/${orderId}/add-items`, {
      items,
    });

    return response.data;
  } catch (error) {
    throw new Error(
      getErrorMessage(error, "Produktet shtesë nuk mund të dërgohen."),
    );
  }
}
export async function transferOrderTable(orderId, newTableId) {
  try {
    const response = await api.patch(`/api/orders/${orderId}/transfer-table`, {
      new_table_id: newTableId,
    });

    return response.data;
  } catch (error) {
    throw new Error(
      getErrorMessage(
        error,
        "Porosia nuk mund të transferohet në tavolinën e re.",
      ),
    );
  }
}
