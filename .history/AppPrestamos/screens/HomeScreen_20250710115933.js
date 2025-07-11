import React from 'react';
import { View, Text, StyleSheet, Image } from 'react-native';

const HomeScreen = () => {
  const clientesCobroHoy = [
    { nombre: 'Juan Pérez', monto: 95000 },
    { nombre: 'María Gómez', monto: 120000 }, // > 6 cifras
    { nombre: 'Carlos Ruiz', monto: 80000 },
  ];

  return (
    <View style={styles.container}>
      <Image source={require('../assets/LogoNE.png')} style={styles.logo} resizeMode="contain" />
      <Text style={styles.title}>¡Bienvenido a tu App de Préstamos!</Text>
      <Text style={styles.subtitle}>Aquí podrás gestionar tus préstamos y finanzas.</Text>

      {/* Recuadro de recordatorio de cobros */}
      <View style={styles.reminderCard}>
        <Text style={styles.reminderTitle}>Clientes a cobrar hoy:</Text>
        {clientesCobroHoy.length === 0 ? (
          <Text style={styles.noClientsText}>No hay clientes para cobrar hoy.</Text>
        ) : (
          clientesCobroHoy.map((cliente, idx) => (
            <View key={idx} style={
              cliente.monto >= 100000
                ? [styles.clientRow, styles.clientRowHigh]
                : styles.clientRow
            }>
              <Text style={styles.clientName}>{cliente.nombre}</Text>
              <Text style={
                cliente.monto >= 100000
                  ? [styles.clientAmount, styles.clientAmountHigh]
                  : styles.clientAmount
              }>
                ${cliente.monto.toLocaleString()}
              </Text>
            </View>
          ))
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f9f9f9',
    padding: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 10,
    color: '#333',
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
  },
  logo: {
    width: 300,
    height: 300,
    marginBottom: 20,
  },
  reminderCard: {
    width: '100%',
    backgroundColor: '#fffbe6',
    borderRadius: 12,
    padding: 18,
    marginBottom: 24,
    marginTop: 10,
    borderWidth: 1,
    borderColor: '#ffe58f',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.07,
    shadowRadius: 4,
    elevation: 2,
  },
  reminderTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#3b82f6',
    marginBottom: 10,
  },
  noClientsText: {
    color: '#888',
    fontStyle: 'italic',
    textAlign: 'center',
  },
  clientRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 6,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  clientRowHigh: {
    backgroundColor: '#fff1f0',
    borderLeftWidth: 5,
    borderLeftColor: '#ef4444',
    borderRadius: 6,
  },
  clientName: {
    fontSize: 16,
    color: '#333',
  },
  clientAmount: {
    fontSize: 16,
    color: '#1e293b',
  },
  clientAmountHigh: {
    color: '#ef4444',
    fontWeight: 'bold',
    fontSize: 17,
  },
});

export default HomeScreen;