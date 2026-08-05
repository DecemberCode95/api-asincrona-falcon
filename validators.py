from typing import Dict, List, Any, Optional


class ProductoValidator:
    @staticmethod
    def validar_creacion(datos: Dict[str, Any]) -> Dict[str, str]:
        """
        Valida los datos para crear un nuevo producto
        
        Args:
            datos: Diccionario con datos del producto
            
        Returns:
            Diccionario con errores encontrados (vacío si es válido)
        """
        errores: Dict[str, str] = {}

        # Validar campo 'nombre'
        nombre: Optional[Any] = datos.get("nombre")
        if not nombre or not isinstance(nombre, str) or len(nombre.strip()) == 0:
            errores["nombre"] = "El campo 'nombre' es obligatorio y debe ser un texto válido."

        # Validar campo 'precio'
        precio: Optional[Any] = datos.get("precio")
        if precio is None or not isinstance(precio, (int, float)) or precio <= 0:
            errores["precio"] = "El campo 'precio' es obligatorio y debe ser un número mayor a 0."

        # Validar campo 'stock'
        stock: Optional[Any] = datos.get("stock")
        if stock is None or not isinstance(stock, int) or stock < 0:
            errores["stock"] = "El campo 'stock' es obligatorio y debe ser un número entero mayor o igual a 0."

        return errores

    