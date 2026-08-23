import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Armchair,
  Banknote,
  ChevronRight,
  CreditCard,
  MapPin,
  Minus,
  Plus,
  Search,
  ShoppingCart,
  Trash2,
  X,
  XCircle,
} from "lucide-react";
import { getTables } from "../../services/tableService";
import "./OrderPanel.css";

import { PRODUCT_CATEGORIES } from "../../constants/productCategories";

import { getProducts } from "../../services/productService";

import {
  addItemsToOrder,
  cancelOrder,
  createOrder,
  getOrderById,
  payOrder,
  transferOrderTable,
  updateOrder,
  updateOrderStatus,
} from "../../services/orderService";

function OrderPanel({ table, onClose, onOrderSaved }) {
  const { t } = useTranslation();
  const [products, setProducts] = useState([]);
  const [orderItems, setOrderItems] = useState([]);
  const [newOrderItems, setNewOrderItems] = useState([]);

  const [tables, setTables] = useState([]);
  const [showTableTransfer, setShowTableTransfer] = useState(false);
  const [selectedTransferTableId, setSelectedTransferTableId] = useState("");
  const [transferringTable, setTransferringTable] = useState(false);

  const [currentOrderId, setCurrentOrderId] = useState(null);
  const [currentOrderStatus, setCurrentOrderStatus] = useState("draft");

  const [searchTerm, setSearchTerm] = useState("");
  const [activeCategory, setActiveCategory] = useState("All");

  const [paymentMethod, setPaymentMethod] = useState("cash");

  const [loadingProducts, setLoadingProducts] = useState(false);
  const [loadingOrder, setLoadingOrder] = useState(false);

  const [sendingToKitchen, setSendingToKitchen] = useState(false);

  const [savingOrder, setSavingOrder] = useState(false);
  const [payingOrder, setPayingOrder] = useState(false);
  const [cancellingOrder, setCancellingOrder] = useState(false);

  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  useEffect(() => {
    if (!table) {
      return;
    }
    async function loadPanelData() {
      try {
        setLoadingProducts(true);
        setLoadingOrder(true);
        setError("");
        setSuccessMessage("");

        const productsData = await getProducts();
        const tablesData = await getTables();

        const productsList = Array.isArray(productsData)
          ? productsData
          : productsData?.products || [];

        const tablesList = Array.isArray(tablesData)
          ? tablesData
          : tablesData?.tables || [];

        setProducts(productsList);
        setTables(tablesList);

        if (table.active_order_id) {
          const existingOrder = await getOrderById(table.active_order_id);

          setCurrentOrderId(existingOrder.id);

          setCurrentOrderStatus(existingOrder.status || "draft");

          setOrderItems(
            existingOrder.items.map((item) => {
              const matchingProduct = productsList.find(
                (product) => getProductId(product) === item.product_id,
              );

              return {
                productId: item.product_id,
                name: item.name,
                price: Number(item.price),
                quantity: item.quantity,
                stock: Number(matchingProduct?.stock ?? 0),
              };
            }),
          );
        } else {
          setCurrentOrderId(null);
          setCurrentOrderStatus("draft");
          setOrderItems([]);
        }
      } catch (err) {
        console.error("Gabim gjatë hapjes së panelit:", err);

        setError(err.message || t("orderPanel.loadError"));
      } finally {
        setLoadingProducts(false);
        setLoadingOrder(false);
      }
    }

    setSearchTerm("");
    setActiveCategory("All");
    setPaymentMethod("cash");

    loadPanelData();
  }, [table]);

  const categories = useMemo(() => {
    return ["All", ...PRODUCT_CATEGORIES];
  }, []);

  const filteredProducts = useMemo(() => {
    const searchValue = searchTerm.trim().toLowerCase();

    return products.filter((product) => {
      const productName = String(product.name || "").toLowerCase();

      const productCategory = String(product.category || "").toLowerCase();

      const matchesSearch =
        productName.includes(searchValue) ||
        productCategory.includes(searchValue);

      const matchesCategory =
        activeCategory === "All" || product.category === activeCategory;

      const isActive = product.is_active !== false;

      return matchesSearch && matchesCategory && isActive;
    });
  }, [products, searchTerm, activeCategory]);

  const freeTables = useMemo(() => {
    if (!table) {
      return [];
    }

    const currentTableId = getTableId(table);

    return tables.filter((item) => {
      const itemId = getTableId(item);

      return (
        itemId &&
        item.status === "free" &&
        item.is_active !== false &&
        itemId !== currentTableId
      );
    });
  }, [tables, table]);

  const totalItems = useMemo(() => {
    const oldItems = orderItems.reduce(
      (total, item) => total + item.quantity,
      0,
    );

    const addedItems = newOrderItems.reduce(
      (total, item) => total + item.quantity,
      0,
    );

    return oldItems + addedItems;
  }, [orderItems, newOrderItems]);

  const totalNewItems = useMemo(() => {
    return newOrderItems.reduce((total, item) => total + item.quantity, 0);
  }, [newOrderItems]);

  const orderTotal = useMemo(() => {
    const oldTotal = orderItems.reduce(
      (total, item) => total + Number(item.price) * item.quantity,
      0,
    );

    const addedTotal = newOrderItems.reduce(
      (total, item) => total + Number(item.price) * item.quantity,
      0,
    );

    return oldTotal + addedTotal;
  }, [orderItems, newOrderItems]);

  const panelIsLoading = loadingProducts || loadingOrder;

  const actionInProgress =
    savingOrder ||
    payingOrder ||
    cancellingOrder ||
    sendingToKitchen ||
    transferringTable;

  const orderIsEditable = !currentOrderId || currentOrderStatus === "draft";

  function getProductId(product) {
    return product.id || product._id;
  }

  function getTableId(selectedTable) {
    return selectedTable?.id || selectedTable?._id || null;
  }

  function resetMessages() {
    setError("");
    setSuccessMessage("");
  }
  async function handleTransferTable() {
    if (!currentOrderId) {
      setError(t("orderPanel.noActiveOrderToTransfer"));
      return;
    }

    if (!selectedTransferTableId) {
      setError(t("orderPanel.selectTableToTransfer"));
      return;
    }

    try {
      setTransferringTable(true);
      setError("");
      setSuccessMessage("");

      const updatedOrder = await transferOrderTable(
        currentOrderId,
        selectedTransferTableId,
      );

      setSuccessMessage(
        t("orderPanel.transferSuccess", {
          table: updatedOrder.table_number,
        }),
      );

      setShowTableTransfer(false);
      setSelectedTransferTableId("");

      if (onOrderSaved) {
        await onOrderSaved(updatedOrder);
      }
    } catch (err) {
      console.error("Transfer table error:", err);

      setError(err.message || t("orderPanel.transferError"));
    } finally {
      setTransferringTable(false);
    }
  }
  async function reloadProducts() {
    const productsData = await getProducts();

    const productsList = Array.isArray(productsData)
      ? productsData
      : productsData?.products || [];

    setProducts(productsList);

    return productsList;
  }

  function handleAddProduct(product) {
    const productId = getProductId(product);
    const stock = Number(product.stock || 0);

    if (!productId) {
      setError(t("orderPanel.invalidProductId"));
      return;
    }

    if (stock <= 0) {
      setError(
        t("orderPanel.outOfStock", {
          product: product.name,
        }),
      );
      return;
    }

    resetMessages();

    // Nëse porosia është dërguar tashmë,
    // produktet e reja ruhen veçmas.
    if (currentOrderId && currentOrderStatus !== "draft") {
      setNewOrderItems((currentItems) => {
        const existingItem = currentItems.find(
          (item) => item.productId === productId,
        );

        if (existingItem) {
          return currentItems.map((item) =>
            item.productId === productId
              ? {
                  ...item,
                  quantity: item.quantity + 1,
                }
              : item,
          );
        }

        return [
          ...currentItems,
          {
            productId,
            name: product.name,
            price: Number(product.price),
            quantity: 1,
            stock,
          },
        ];
      });

      return;
    }

    // Nëse është draft, vazhdon normalisht.
    setOrderItems((currentItems) => {
      const existingItem = currentItems.find(
        (item) => item.productId === productId,
      );

      if (existingItem) {
        return currentItems.map((item) =>
          item.productId === productId
            ? {
                ...item,
                quantity: item.quantity + 1,
              }
            : item,
        );
      }

      return [
        ...currentItems,
        {
          productId,
          name: product.name,
          price: Number(product.price),
          quantity: 1,
          stock,
        },
      ];
    });
  }

  function handleIncreaseQuantity(productId) {
    if (!orderIsEditable) {
      setError(t("orderPanel.orderNotEditable"));
      return;
    }

    resetMessages();

    setOrderItems((currentItems) => {
      const existingItem = currentItems.find(
        (item) => item.productId === productId,
      );

      if (!existingItem) {
        return currentItems;
      }

      const product = products.find(
        (currentProduct) => getProductId(currentProduct) === productId,
      );

      const stock = Number(product?.stock ?? existingItem.stock ?? 0);

      if (stock <= 0) {
        setError(
          t("orderPanel.outOfStock", {
            product: existingItem.name,
          }),
        );

        return currentItems;
      }

      if (existingItem.quantity >= stock) {
        setError(
          t("orderPanel.notEnoughStock", {
            product: existingItem.name,
            stock,
          }),
        );

        return currentItems;
      }

      return currentItems.map((item) =>
        item.productId === productId
          ? {
              ...item,
              quantity: item.quantity + 1,
              stock,
            }
          : item,
      );
    });
  }

  function handleDecreaseQuantity(productId) {
    if (!orderIsEditable) {
      setError(t("orderPanel.orderNotEditable"));
      return;
    }

    resetMessages();

    setOrderItems((currentItems) =>
      currentItems
        .map((item) =>
          item.productId === productId
            ? {
                ...item,
                quantity: item.quantity - 1,
              }
            : item,
        )
        .filter((item) => item.quantity > 0),
    );
  }

  function handleRemoveItem(productId) {
    if (!orderIsEditable) {
      setError(t("orderPanel.orderNotEditable"));
      return;
    }

    resetMessages();

    setOrderItems((currentItems) =>
      currentItems.filter((item) => item.productId !== productId),
    );
  }

  function handleClearOrder() {
    if (!orderIsEditable) {
      setError(t("orderPanel.orderNotEditable"));
      return;
    }

    setOrderItems([]);
    resetMessages();
  }
  function handleIncreaseNewItem(productId) {
    resetMessages();

    setNewOrderItems((currentItems) =>
      currentItems.map((item) => {
        if (item.productId !== productId) {
          return item;
        }

        const product = products.find(
          (currentProduct) => getProductId(currentProduct) === productId,
        );

        const stock = Number(product?.stock ?? item.stock ?? 0);

        if (item.quantity >= stock) {
          setError(
            t("orderPanel.notEnoughStock", {
              product: item.name,
              stock,
            }),
          );

          return item;
        }

        return {
          ...item,
          quantity: item.quantity + 1,
          stock,
        };
      }),
    );
  }

  function handleDecreaseNewItem(productId) {
    resetMessages();

    setNewOrderItems((currentItems) =>
      currentItems
        .map((item) =>
          item.productId === productId
            ? {
                ...item,
                quantity: item.quantity - 1,
              }
            : item,
        )
        .filter((item) => item.quantity > 0),
    );
  }

  function handleRemoveNewItem(productId) {
    resetMessages();

    setNewOrderItems((currentItems) =>
      currentItems.filter((item) => item.productId !== productId),
    );
  }

  function createItemsPayload() {
    return orderItems.map((item) => ({
      product_id: item.productId,
      quantity: item.quantity,
    }));
  }

  async function refreshTables(savedOrder) {
    if (typeof onOrderSaved === "function") {
      await onOrderSaved(savedOrder);
    }
  }

  async function handleSaveOrder() {
    if (!table) {
      setError(t("orderPanel.onlyDraftEditable"));
      return;
    }

    if (!orderIsEditable) {
      setError(t("orderPanel.addAtLeastOneProduct"));
      return;
    }

    if (orderItems.length === 0) {
      setError(t("orderPanel.tableIdMissing"));
      return;
    }

    const tableId = getTableId(table);

    if (!tableId) {
      setError(t("orderPanel.tableIdMissing"));
      return;
    }

    try {
      setSavingOrder(true);
      resetMessages();

      const items = createItemsPayload();

      let savedOrder;

      if (currentOrderId) {
        savedOrder = await updateOrder(currentOrderId, {
          items,
        });
      } else {
        savedOrder = await createOrder({
          table_id: tableId,
          items,
        });

        setCurrentOrderId(savedOrder.id);
      }

      setCurrentOrderStatus(savedOrder.status || "draft");

      await refreshTables(savedOrder);

      setSuccessMessage(
        currentOrderId
          ? t("orderPanel.orderUpdated", {
              total: Number(savedOrder.total).toFixed(2),
            })
          : t("orderPanel.orderSaved", {
              total: Number(savedOrder.total).toFixed(2),
            }),
      );

      window.setTimeout(() => {
        onClose();
      }, 1000);
    } catch (err) {
      console.error("Gabim gjatë ruajtjes:", err);

      setError(err.message || t("orderPanel.orderSaveError"));
    } finally {
      setSavingOrder(false);
    }
  }

  async function handleSendAddedItems() {
    if (!currentOrderId) {
      setError(t("orderPanel.noActiveOrder"));
      return;
    }

    if (newOrderItems.length === 0) {
      setError(t("orderPanel.addAtLeastOneNewProduct"));
      return;
    }

    try {
      setSavingOrder(true);
      resetMessages();

      const items = newOrderItems.map((item) => ({
        product_id: item.productId,
        quantity: item.quantity,
      }));

      const updatedOrder = await addItemsToOrder(currentOrderId, items);

      setOrderItems(
        updatedOrder.items.map((item) => ({
          productId: item.product_id,
          name: item.name,
          price: Number(item.price),
          quantity: item.quantity,
        })),
      );

      setNewOrderItems([]);

      setCurrentOrderStatus(updatedOrder.status || "sent_to_kitchen");

      await reloadProducts();
      await refreshTables(updatedOrder);

      setSuccessMessage(
        t("orderPanel.addedItemsSent", {
          total: Number(updatedOrder.total).toFixed(2),
        }),
      );
    } catch (err) {
      console.error("Gabim gjatë shtimit të produkteve:", err);

      setError(err.message || t("orderPanel.addedItemsSendError"));
    } finally {
      setSavingOrder(false);
    }
  }

  async function handleSendToKitchen() {
    if (!currentOrderId) {
      setError(t("orderPanel.saveBeforeSend"));
      return;
    }

    if (currentOrderStatus !== "draft") {
      setError(t("orderPanel.onlyDraftCanBeSent"));
      return;
    }

    try {
      setSendingToKitchen(true);
      resetMessages();

      const updatedOrder = await updateOrderStatus(
        currentOrderId,
        "sent_to_kitchen",
      );

      setCurrentOrderStatus(updatedOrder.status);

      /*
       * Send Order e zbret stock-un në backend.
       * Prandaj e rifreskojmë listën e produkteve
       * që frontend-i ta shfaqë stock-un e ri.
       */
      await reloadProducts();

      await refreshTables(updatedOrder);

      setSuccessMessage(t("orderPanel.orderSent"));
    } catch (err) {
      console.error("Gabim gjatë dërgimit të porosisë:", err);

      setError(err.message || t("orderPanel.orderSendError"));
    } finally {
      setSendingToKitchen(false);
    }
  }

  async function handlePayOrder() {
    if (!currentOrderId) {
      setError(t("orderPanel.saveBeforePayment"));
      return;
    }

    try {
      setPayingOrder(true);
      resetMessages();

      const paidOrder = await payOrder(currentOrderId, paymentMethod);

      await refreshTables(paidOrder);

      setSuccessMessage(
        t("orderPanel.paymentCompleted", {
          method:
            paymentMethod === "cash"
              ? t("orderPanel.cash")
              : t("orderPanel.card"),
          total: Number(paidOrder.total).toFixed(2),
        }),
      );

      window.setTimeout(() => {
        onClose();
      }, 1200);
    } catch (err) {
      console.error("Gabim gjatë pagesës:", err);

      setError(err.message || t("orderPanel.paymentError"));
    } finally {
      setPayingOrder(false);
    }
  }

  async function handleCancelOrder() {
    if (!currentOrderId) {
      setError(t("orderPanel.noActiveOrderToCancel"));
      return;
    }

    const confirmed = window.confirm(t("orderPanel.cancelConfirm"));

    if (!confirmed) {
      return;
    }

    try {
      setCancellingOrder(true);
      resetMessages();

      const cancelledOrder = await cancelOrder(currentOrderId);

      /*
       * Cancel Order e rikthen stock-un
       * në backend, prandaj rifreskojmë
       * edhe produktet.
       */
      await reloadProducts();

      await refreshTables(cancelledOrder);

      setSuccessMessage(t("orderPanel.cancelSuccess"));

      window.setTimeout(() => {
        onClose();
      }, 1000);
    } catch (err) {
      console.error("Gabim gjatë anulimit të porosisë:", err);

      setError(err.message || t("orderPanel.cancelError"));
    } finally {
      setCancellingOrder(false);
    }
  }

  if (!table) {
    return null;
  }

  return (
    <div
      className="order-panel-overlay"
      onClick={actionInProgress ? undefined : onClose}
    >
      <aside
        className="order-panel"
        onClick={(event) => event.stopPropagation()}
      >
        <header className="order-panel-header">
          <div>
            <p className="order-panel-eyebrow">
              {currentOrderId
                ? `${t("orderPanel.orderStatus")}: ${t(
                    `orderPanel.status.${currentOrderStatus}`,
                  )}`
                : t("orderPanel.newOrder")}
            </p>

            <h2>
              {t("orderPanel.table")} {table.number}
            </h2>
          </div>

          <button
            type="button"
            className="order-panel-close"
            onClick={onClose}
            disabled={actionInProgress}
          >
            <X size={22} />
          </button>
        </header>

        <div className="order-table-info">
          <div className="order-table-icon">
            <Armchair size={27} />
          </div>

          <div className="order-table-text">
            <h3>
              {t("orderPanel.table")} {table.number}
            </h3>

            <p>
              <MapPin size={15} />
              t(`zones.${table.zone}`)
            </p>
          </div>

          <span className={`order-status order-status-${table.status}`}>
            {t(`tables.${table.status}`)}
          </span>
        </div>

        {error && (
          <div className="order-api-message order-api-error">{error}</div>
        )}

        {successMessage && (
          <div className="order-api-message order-api-success">
            {successMessage}
          </div>
        )}

        <div className="order-workspace">
          <section className="products-section">
            <div className="product-search">
              <Search size={18} />

              <input
                type="text"
                value={searchTerm}
                placeholder={t("orderPanel.searchProducts")}
                onChange={(event) => setSearchTerm(event.target.value)}
              />

              {searchTerm && (
                <button type="button" onClick={() => setSearchTerm("")}>
                  <X size={16} />
                </button>
              )}
            </div>

            <div className="category-list">
              {categories.map((category) => (
                <button
                  key={category}
                  type="button"
                  className={
                    activeCategory === category
                      ? "category-button category-button-active"
                      : "category-button"
                  }
                  onClick={() => setActiveCategory(category)}
                >
                  {category === "All" ? t("orderPanel.all") : category}
                </button>
              ))}
            </div>

            {panelIsLoading ? (
              <div className="order-loading">{t("orderPanel.loading")}</div>
            ) : filteredProducts.length === 0 ? (
              <div className="order-loading">
                {t("orderPanel.noProductsInCategory")}
              </div>
            ) : (
              <div className="products-order-grid">
                {filteredProducts.map((product) => {
                  const productId = getProductId(product);

                  const productInOrder = newOrderItems.find(
                    (item) => item.productId === productId,
                  );

                  const stock = Number(product.stock || 0);

                  const isOutOfStock = stock <= 0;

                  const isLowStock = stock > 0 && stock <= 10;

                  const selectedQuantity = productInOrder?.quantity || 0;

                  const reachedStockLimit = selectedQuantity >= stock;

                  return (
                    <button
                      key={productId}
                      type="button"
                      className={
                        isOutOfStock
                          ? "order-product-card order-product-card-out"
                          : "order-product-card"
                      }
                      disabled={
                        actionInProgress || isOutOfStock || reachedStockLimit
                      }
                      onClick={() => handleAddProduct(product)}
                    >
                      <div className="order-product-top">
                        <span className="product-category">
                          {product.category}
                        </span>

                        {productInOrder && (
                          <span className="product-quantity-badge">
                            {productInOrder.quantity}
                          </span>
                        )}
                      </div>

                      <h3>{product.name}</h3>

                      {isOutOfStock ? (
                        <span className="order-stock-status order-stock-out">
                          {t("orderPanel.outOfStockLabel")}
                        </span>
                      ) : isLowStock ? (
                        <span className="order-stock-status order-stock-low">
                          {t("orderPanel.onlyStockLeft", { stock })}
                        </span>
                      ) : (
                        <span className="order-stock-status order-stock-good">
                          {t("orderPanel.stock", { stock })}
                        </span>
                      )}

                      <div className="order-product-bottom">
                        <strong>€{Number(product.price).toFixed(2)}</strong>

                        <span className="add-product-icon">
                          <Plus size={17} />
                        </span>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </section>

          <section className="cart-section">
            <div className="cart-header">
              <div>
                <h3>{t("orderPanel.currentOrder")}</h3>

                <p>
                  {totalItems} {t("orderPanel.items")}
                </p>
              </div>

              {orderItems.length > 0 && (
                <button
                  type="button"
                  className="clear-order-button"
                  disabled={actionInProgress || !orderIsEditable}
                  onClick={handleClearOrder}
                >
                  {t("orderPanel.clear")}
                </button>
              )}
            </div>

            {orderItems.length === 0 ? (
              <div className="empty-order">
                <div className="empty-order-icon">
                  <ShoppingCart size={32} />
                </div>
                <h3>{t("orderPanel.noProductsAdded")}</h3>
              </div>
            ) : (
              <div className="order-items-list">
                {orderItems.map((item, index) => {
                  const product = products.find(
                    (currentProduct) =>
                      getProductId(currentProduct) === item.productId,
                  );

                  const availableStock = Number(
                    product?.stock ?? item.stock ?? 0,
                  );

                  const maxReached = item.quantity >= availableStock;

                  return (
                    <article
                      key={`${item.productId}-${index}`}
                      className="order-item"
                    >
                      <div className="order-item-main">
                        <div>
                          <h4>{item.name}</h4>

                          <p>€{item.price.toFixed(2)}</p>

                          {availableStock <= 10 ? (
                            <small className="order-item-stock-warning">
                              {t("orderPanel.stock", {
                                stock: availableStock,
                              })}
                            </small>
                          ) : null}
                        </div>

                        <strong>
                          €{(item.price * item.quantity).toFixed(2)}
                        </strong>
                      </div>

                      <div className="order-item-actions">
                        <div className="quantity-controls">
                          <button
                            type="button"
                            disabled={actionInProgress || !orderIsEditable}
                            onClick={() =>
                              handleDecreaseQuantity(item.productId)
                            }
                          >
                            <Minus size={15} />
                          </button>

                          <span>{item.quantity}</span>

                          <button
                            type="button"
                            disabled={actionInProgress || maxReached}
                            onClick={() => {
                              if (orderIsEditable) {
                                handleIncreaseQuantity(item.productId);
                              } else if (product) {
                                handleAddProduct(product);
                              }
                            }}
                          >
                            <Plus size={15} />
                          </button>
                        </div>

                        <button
                          type="button"
                          className="remove-order-item"
                          disabled={actionInProgress || !orderIsEditable}
                          onClick={() => handleRemoveItem(item.productId)}
                        >
                          <Trash2 size={17} />
                        </button>
                      </div>
                    </article>
                  );
                })}
              </div>
            )}
            {currentOrderId &&
              currentOrderStatus !== "draft" &&
              newOrderItems.length > 0 && (
                <div className="added-items-section">
                  <div className="added-items-header">
                    <div>
                      <h4>{t("orderPanel.newItems")}</h4>
                      <p>{t("orderPanel.notSentYetDescription")}</p>
                    </div>

                    <span>{totalNewItems}</span>
                  </div>

                  <div className="order-items-list">
                    {newOrderItems.map((item) => {
                      const product = products.find(
                        (currentProduct) =>
                          getProductId(currentProduct) === item.productId,
                      );

                      const availableStock = Number(
                        product?.stock ?? item.stock ?? 0,
                      );

                      const maxReached = item.quantity >= availableStock;

                      return (
                        <article
                          key={`new-${item.productId}`}
                          className="order-item new-order-item"
                        >
                          <div className="order-item-main">
                            <div>
                              <h4>{item.name}</h4>

                              <p>€{Number(item.price).toFixed(2)}</p>

                              <small className="new-item-label">
                                {t("orderPanel.notSentYet")}
                              </small>
                            </div>

                            <strong>
                              €{(Number(item.price) * item.quantity).toFixed(2)}
                            </strong>
                          </div>

                          <div className="order-item-actions">
                            <div className="quantity-controls">
                              <button
                                type="button"
                                disabled={actionInProgress}
                                onClick={() =>
                                  handleDecreaseNewItem(item.productId)
                                }
                              >
                                <Minus size={15} />
                              </button>

                              <span>{item.quantity}</span>

                              <button
                                type="button"
                                disabled={actionInProgress || maxReached}
                                onClick={() =>
                                  handleIncreaseNewItem(item.productId)
                                }
                              >
                                <Plus size={15} />
                              </button>
                            </div>

                            <button
                              type="button"
                              className="remove-order-item"
                              disabled={actionInProgress}
                              onClick={() =>
                                handleRemoveNewItem(item.productId)
                              }
                            >
                              <Trash2 size={17} />
                            </button>
                          </div>
                        </article>
                      );
                    })}
                  </div>
                </div>
              )}
            {currentOrderId && (
              <div className="category-list">
                <button
                  type="button"
                  className={
                    paymentMethod === "cash"
                      ? "category-button category-button-active"
                      : "category-button"
                  }
                  onClick={() => setPaymentMethod("cash")}
                >
                  <Banknote size={16} />
                  {t("orderPanel.cash")}
                </button>

                <button
                  type="button"
                  className={
                    paymentMethod === "card"
                      ? "category-button category-button-active"
                      : "category-button"
                  }
                  onClick={() => setPaymentMethod("card")}
                >
                  <CreditCard size={16} />
                  Card
                </button>
              </div>
            )}
          </section>
        </div>

        <footer className="order-panel-footer">
          <div className="order-total-row">
            <div>
              <span>{t("orderPanel.total")}</span>

              <small>
                {totalItems} {t("orderPanel.items")}
              </small>
            </div>

            <strong>€{orderTotal.toFixed(2)}</strong>
          </div>

          {currentOrderId ? (
            <>
              {currentOrderStatus === "draft" && (
                <button
                  type="button"
                  className="send-kitchen-button"
                  disabled={orderItems.length === 0 || actionInProgress}
                  onClick={handleSendToKitchen}
                >
                  {sendingToKitchen
                    ? t("orderPanel.sendingOrder")
                    : t("orderPanel.sendOrder")}
                </button>
              )}

              {currentOrderId &&
                currentOrderStatus !== "draft" &&
                newOrderItems.length > 0 && (
                  <button
                    type="button"
                    className="send-kitchen-button"
                    disabled={actionInProgress}
                    onClick={handleSendAddedItems}
                  >
                    {t("orderPanel.sendAddedItems", {
                      count: totalNewItems,
                    })}
                  </button>
                )}

              <button
                type="button"
                className="save-order-button"
                disabled={
                  orderItems.length === 0 ||
                  actionInProgress ||
                  currentOrderStatus !== "draft"
                }
                onClick={handleSaveOrder}
              >
                {savingOrder
                  ? t("orderPanel.saving")
                  : t("orderPanel.saveDraft")}

                {!savingOrder && <ChevronRight size={18} />}
              </button>

              <button
                type="button"
                className="save-order-button"
                disabled={orderItems.length === 0 || actionInProgress}
                onClick={handlePayOrder}
                style={{
                  marginTop: "10px",
                }}
              >
                {payingOrder
                  ? t("orderPanel.processingPayment")
                  : t("orderPanel.payWith", {
                      method:
                        paymentMethod === "cash"
                          ? t("orderPanel.cash")
                          : t("orderPanel.card"),
                    })}
              </button>

              {currentOrderStatus !== "paid" &&
                currentOrderStatus !== "cancelled" && (
                  <>
                    <button
                      type="button"
                      className="save-order-button"
                      disabled={actionInProgress}
                      onClick={() => {
                        setShowTableTransfer((currentValue) => !currentValue);
                        setSelectedTransferTableId("");
                        resetMessages();
                      }}
                      style={{
                        marginTop: "10px",
                      }}
                    >
                      <Armchair size={18} />
                      {t("orderPanel.changeTable")}
                    </button>

                    {showTableTransfer && (
                      <div className="table-transfer-box">
                        <div className="table-transfer-header">
                          <div>
                            <strong>{t("orderPanel.changeTableTitle")}</strong>
                            <p>{t("orderPanel.changeTableDescription")}</p>
                          </div>

                          <button
                            type="button"
                            onClick={() => {
                              setShowTableTransfer(false);
                              setSelectedTransferTableId("");
                            }}
                            disabled={transferringTable}
                            aria-label={t("orderPanel.close")}
                          >
                            <X size={18} />
                          </button>
                        </div>

                        {freeTables.length === 0 ? (
                          <p>{t("orderPanel.noFreeTables")}</p>
                        ) : (
                          <>
                            <div className="table-transfer-options">
                              {freeTables.map((freeTable) => {
                                const tableId = getTableId(freeTable);
                                const isSelected =
                                  selectedTransferTableId === tableId;

                                return (
                                  <button
                                    key={tableId}
                                    type="button"
                                    className={`table-transfer-option ${
                                      isSelected ? "selected" : ""
                                    }`}
                                    onClick={() =>
                                      setSelectedTransferTableId(tableId)
                                    }
                                    disabled={transferringTable}
                                  >
                                    <span>
                                      {t("orderPanel.table")} {freeTable.number}
                                    </span>

                                    <small>
                                      {t(`zones.${freeTable.zone}`)}
                                    </small>
                                  </button>
                                );
                              })}
                            </div>

                            <button
                              type="button"
                              className="save-order-button"
                              onClick={handleTransferTable}
                              disabled={
                                !selectedTransferTableId || transferringTable
                              }
                              style={{
                                marginTop: "10px",
                              }}
                            >
                              {transferringTable
                                ? t("orderPanel.transferringTable")
                                : t("orderPanel.confirmTransfer")}
                            </button>
                          </>
                        )}
                      </div>
                    )}
                  </>
                )}

              <button
                type="button"
                className="cancel-order-button"
                disabled={actionInProgress}
                onClick={handleCancelOrder}
              >
                <XCircle size={18} />

                {cancellingOrder
                  ? t("orderPanel.cancelling")
                  : t("orderPanel.cancelOrder")}
              </button>
            </>
          ) : (
            <button
              type="button"
              className="save-order-button"
              disabled={orderItems.length === 0 || actionInProgress}
              onClick={handleSaveOrder}
            >
              {savingOrder ? t("orderPanel.saving") : t("orderPanel.saveDraft")}

              {!savingOrder && <ChevronRight size={18} />}
            </button>
          )}
        </footer>
      </aside>
    </div>
  );
}

export default OrderPanel;
